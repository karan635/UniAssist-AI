from pathlib import Path
from typing import List, Optional
import re

import pdfplumber

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.config import settings
from app.services.knowledge.metadata_builder import MetadataBuilder


class PDFLoaderService:
    """
    Smart PDF loader for UniAssist-AI.

    Normal PDFs:
        PyPDFLoader

    Placement PDFs:
        pdfplumber table extraction
        + structured placement text
    """

    def __init__(self, documents_path: Optional[str] = None):

        self.documents_path = Path(
            documents_path or settings.DOCUMENT_PATH
        )

        self.metadata_builder = MetadataBuilder()

    # =========================================================
    # MAIN LOADER
    # =========================================================

    def load_documents(self) -> List[Document]:

        all_docs: List[Document] = []

        pdf_files = sorted(
            self.documents_path.rglob("*.pdf")
        )

        if not pdf_files:
            print(
                f"[WARNING] No PDF files found in: "
                f"{self.documents_path}"
            )

        for pdf in pdf_files:

            try:

                print(f"\n[PDF] Loading: {pdf.name}")

                # -------------------------------------------------
                # Placement PDFs
                # -------------------------------------------------

                if self._is_placement_pdf(pdf):

                    docs = self._load_placement_pdf(pdf)

                # -------------------------------------------------
                # Normal PDFs
                # -------------------------------------------------

                else:

                    docs = self._load_normal_pdf(pdf)

                # -------------------------------------------------
                # Metadata
                # -------------------------------------------------

                metadata = self.metadata_builder.build(pdf)

                for doc in docs:

                    doc.metadata.update(metadata)

                    # Make sure filename is always available
                    doc.metadata["filename"] = pdf.name

                    # Make category available
                    doc.metadata["category"] = pdf.parent.name

                all_docs.extend(docs)

                print(
                    f"[SUCCESS] {pdf.name} -> "
                    f"{len(docs)} document(s)"
                )

            except Exception as e:

                print(
                    f"[ERROR] Failed to load "
                    f"{pdf.name}: {e}"
                )

        print(
            f"\n[TOTAL] Documents/pages loaded: "
            f"{len(all_docs)}"
        )

        return all_docs

    # =========================================================
    # DETECT PLACEMENT PDF
    # =========================================================

    def _is_placement_pdf(self, pdf: Path) -> bool:

        filename = pdf.name.lower()

        return (
            filename.startswith("placement_")
            or "placement" in filename
        )

    # =========================================================
    # NORMAL PDF
    # =========================================================

    def _load_normal_pdf(
        self,
        pdf: Path
    ) -> List[Document]:

        loader = PyPDFLoader(str(pdf))

        return loader.load()

    # =========================================================
    # PLACEMENT PDF
    # =========================================================

    def _load_placement_pdf(
        self,
        pdf: Path
    ) -> List[Document]:

        documents: List[Document] = []

        with pdfplumber.open(str(pdf)) as pdf_file:

            for page_number, page in enumerate(
                pdf_file.pages
            ):

                # -------------------------------------------------
                # Extract tables
                # -------------------------------------------------

                tables = page.extract_tables()

                # -------------------------------------------------
                # Extract normal text too
                # -------------------------------------------------

                raw_text = page.extract_text() or ""

                structured_text = (
                    self._build_placement_text(
                        raw_text=raw_text,
                        tables=tables
                    )
                )

                if not structured_text.strip():
                    continue

                document = Document(
                    page_content=structured_text,
                    metadata={
                        "page": page_number,
                        "page_label": str(
                            page_number + 1
                        ),
                        "document_type": "placement",
                    }
                )

                documents.append(document)

        return documents

    # =========================================================
    # BUILD STRUCTURED PLACEMENT TEXT
    # =========================================================

    def _build_placement_text(
        self,
        raw_text: str,
        tables: List
    ) -> str:

        year = self._extract_year(raw_text)

        output = []

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        output.append(
            "PLACEMENT INFORMATION"
        )

        if year:

            output.append(
                f"Placement Year: {year}"
            )

        output.append(
            "Document Type: Company-wise and "
            "Branch-wise Placement Data"
        )

        output.append("")

        # -----------------------------------------------------
        # Extract table information
        # -----------------------------------------------------

        if tables:

            for table in tables:

                cleaned_rows = []

                for row in table:

                    if not row:
                        continue

                    cleaned_row = []

                    for cell in row:

                        if cell is None:
                            cell = ""

                        cell = str(cell)

                        cell = re.sub(
                            r"\s+",
                            " ",
                            cell
                        ).strip()

                        cleaned_row.append(cell)

                    if any(cleaned_row):

                        cleaned_rows.append(
                            cleaned_row
                        )

                if not cleaned_rows:
                    continue

                structured_table = (
                    self._format_placement_table(
                        cleaned_rows
                    )
                )

                if structured_table:

                    output.append(
                        structured_table
                    )

        # -----------------------------------------------------
        # Extract important summary information
        # -----------------------------------------------------

        summary = self._extract_summary(
            raw_text
        )

        if summary:

            output.append("")
            output.append(
                "PLACEMENT SUMMARY"
            )

            output.extend(summary)

        # -----------------------------------------------------
        # Fallback raw text
        # -----------------------------------------------------

        if not tables:

            output.append("")
            output.append(
                "SOURCE TEXT"
            )
            output.append(raw_text)

        return "\n".join(output)

    # =========================================================
    # FORMAT TABLE
    # =========================================================

    def _format_placement_table(
        self,
        rows: List[List[str]]
    ) -> str:

        output = []

        headers = None

        # Find useful header row
        for row in rows:

            row_text = " ".join(row).lower()

            if (
                "recruiter" in row_text
                or "computer" in row_text
                or "mca" in row_text
            ):

                headers = row
                break

        # -----------------------------------------------------
        # Generic table representation
        # -----------------------------------------------------

        if headers:

            output.append(
                "PLACEMENT COMPANY DATA"
            )

            output.append(
                "Columns: "
                + " | ".join(headers)
            )

        else:

            output.append(
                "PLACEMENT TABLE"
            )

        # -----------------------------------------------------
        # Add every row
        # -----------------------------------------------------

        for row in rows:

            row_text = " | ".join(
                cell for cell in row
                if cell
            )

            if not row_text:
                continue

            output.append(
                row_text
            )

        return "\n".join(output)

    # =========================================================
    # EXTRACT YEAR
    # =========================================================

    def _extract_year(
        self,
        text: str
    ):

        match = re.search(
            r"batch(?:\s+passing\s+out\s+batch)?\s+in\s+(20\d{2})",
            text,
            re.IGNORECASE
        )

        if match:

            return int(match.group(1))

        # fallback
        match = re.search(
            r"\b(20\d{2})\b",
            text
        )

        if match:

            return int(match.group(1))

        return None

    # =========================================================
    # EXTRACT SUMMARY
    # =========================================================

    def _extract_summary(
        self,
        text: str
    ) -> List[str]:

        summary = []

        patterns = {

            "Maximum Package":
                r"MAXIMUM PACKAGE OFFERED\s*([\d.]+\s*LPA)",

            "Minimum Package":
                r"MINIMUM PACKAGE OFFERED\s*([\d.]+(?:\s*LPA)?)",

            "Average Package":
                r"AVERAGE PACKAGE OFFERED\s*([\d.]+(?:\s*LPA)?)",

        }

        for label, pattern in patterns.items():

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                summary.append(
                    f"{label}: {value}"
                )

        # -----------------------------------------------------
        # Total offers
        # -----------------------------------------------------

        total_match = re.search(
            r"TOTAL OFFERS\s+([\d\s]+)",
            text,
            re.IGNORECASE
        )

        if total_match:

            summary.append(
                "Total Offers: "
                + total_match.group(1).strip()
            )

        # -----------------------------------------------------
        # Eligible students
        # -----------------------------------------------------

        eligible_match = re.search(
            r"ELIGIBLE STUDENTS\s+([\d\s]+)",
            text,
            re.IGNORECASE
        )

        if eligible_match:

            summary.append(
                "Eligible Students: "
                + eligible_match.group(1).strip()
            )

        return summary