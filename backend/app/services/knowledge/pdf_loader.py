"""Smart PDF loader for UniAssist-AI.

Normal PDFs -> PyPDFLoader
Placement PDFs -> pdfplumber table extraction + structured text
"""

import re
from pathlib import Path
from typing import List, Optional

import pdfplumber
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.config import settings
from app.services.knowledge.metadata_builder import MetadataBuilder


class PDFLoaderService:

    def __init__(self, documents_path: Optional[str] = None):
        self.documents_path = Path(documents_path or settings.DOCUMENT_PATH)
        self.metadata_builder = MetadataBuilder()

    # ---------------------------------------------------------------
    # MAIN LOADER
    # ---------------------------------------------------------------

    def load_documents(self) -> List[Document]:
        all_docs: List[Document] = []
        pdf_files = sorted(self.documents_path.rglob("*.pdf"))

        if not pdf_files:
            print(f"[WARNING] No PDF files found in: {self.documents_path}")

        for pdf in pdf_files:
            try:
                print(f"\n[PDF] Loading: {pdf.name}")

                docs = (
                    self._load_placement_pdf(pdf)
                    if self._is_placement_pdf(pdf)
                    else PyPDFLoader(str(pdf)).load()
                )

                metadata = self.metadata_builder.build(pdf)
                for doc in docs:
                    doc.metadata.update(metadata)
                    doc.metadata["filename"] = pdf.name
                    doc.metadata["category"] = pdf.parent.name

                all_docs.extend(docs)
                print(f"[SUCCESS] {pdf.name} -> {len(docs)} document(s)")

            except Exception as e:
                print(f"[ERROR] Failed to load {pdf.name}: {e}")

        print(f"\n[TOTAL] Documents/pages loaded: {len(all_docs)}")
        return all_docs

    def _is_placement_pdf(self, pdf: Path) -> bool:
        return "placement" in pdf.name.lower()

    # ---------------------------------------------------------------
    # PLACEMENT PDFs
    # ---------------------------------------------------------------

    def _load_placement_pdf(self, pdf: Path) -> List[Document]:
        documents = []

        with pdfplumber.open(str(pdf)) as pdf_file:
            for page_number, page in enumerate(pdf_file.pages):
                raw_text = page.extract_text() or ""
                tables = page.extract_tables()
                structured_text = self._build_placement_text(raw_text, tables)

                if not structured_text.strip():
                    continue

                documents.append(Document(
                    page_content=structured_text,
                    metadata={
                        "page": page_number,
                        "page_label": str(page_number + 1),
                        "document_type": "placement",
                    }
                ))

        return documents

    def _build_placement_text(self, raw_text: str, tables: List) -> str:
        year = self._extract_year(raw_text)

        output = [
            "PLACEMENT INFORMATION",
            *([f"Placement Year: {year}"] if year else []),
            "Document Type: Company-wise and Branch-wise Placement Data",
            "",
        ]

        for table in tables:
            cleaned_rows = [
                [re.sub(r"\s+", " ", str(cell or "")).strip() for cell in row]
                for row in table if row
            ]
            cleaned_rows = [row for row in cleaned_rows if any(row)]

            if cleaned_rows:
                output.append(self._format_placement_table(cleaned_rows))

        summary = self._extract_summary(raw_text)
        if summary:
            output += ["", "PLACEMENT SUMMARY", *summary]

        if not tables:
            output += ["", "SOURCE TEXT", raw_text]

        return "\n".join(output)

    def _format_placement_table(self, rows: List[List[str]]) -> str:
        headers = next(
            (row for row in rows
             if any(k in " ".join(row).lower() for k in ("recruiter", "computer", "mca"))),
            None
        )

        output = (
            ["PLACEMENT COMPANY DATA", "Columns: " + " | ".join(headers)]
            if headers else ["PLACEMENT TABLE"]
        )

        output += [
            " | ".join(cell for cell in row if cell)
            for row in rows if any(row)
        ]

        return "\n".join(output)

    # ---------------------------------------------------------------
    # REGEX EXTRACTION
    # ---------------------------------------------------------------

    def _extract_year(self, text: str):
        match = (
            re.search(r"batch(?:\s+passing\s+out\s+batch)?\s+in\s+(20\d{2})", text, re.IGNORECASE)
            or re.search(r"\b(20\d{2})\b", text)
        )
        return int(match.group(1)) if match else None

    def _extract_summary(self, text: str) -> List[str]:
        patterns = {
            "Maximum Package": r"MAXIMUM PACKAGE OFFERED\s*([\d.]+\s*LPA)",
            "Minimum Package": r"MINIMUM PACKAGE OFFERED\s*([\d.]+(?:\s*LPA)?)",
            "Average Package": r"AVERAGE PACKAGE OFFERED\s*([\d.]+(?:\s*LPA)?)",
        }

        summary = [
            f"{label}: {m.group(1).strip()}"
            for label, pattern in patterns.items()
            if (m := re.search(pattern, text, re.IGNORECASE))
        ]

        for label, pattern in (
            ("Total Offers", r"TOTAL OFFERS\s+([\d\s]+)"),
            ("Eligible Students", r"ELIGIBLE STUDENTS\s+([\d\s]+)"),
        ):
            if (m := re.search(pattern, text, re.IGNORECASE)):
                summary.append(f"{label}: {m.group(1).strip()}")

        return summary  