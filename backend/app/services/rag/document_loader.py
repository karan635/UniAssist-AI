"""Document ingestion utilities for the RAG pipeline."""

from pathlib import Path
from typing import List

import os
import platform
import re
import shutil

import fitz  # PyMuPDF
import pdfplumber
import pytesseract

from PIL import Image

# The Tesseract binary is only at a fixed path on Windows dev machines.
# On Linux/Docker it's installed via the OS package manager (apt-get install
# tesseract-ocr) and is already resolvable on PATH, so pytesseract's default
# lookup works unmodified there. Hardcoding the Windows path unconditionally
# broke OCR fallback (TesseractNotFoundError) on every non-Windows deployment.
_WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if platform.system() == "Windows" and not shutil.which("tesseract"):
    if os.path.exists(_WINDOWS_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_TESSERACT_PATH

from langchain_core.documents import Document

import builtins as _builtins

from app.core.config import settings
from app.core.logger import logger
from app.utils.text_matching import is_academic_calendar_filename


# Gate the existing debug print()s (below) behind settings.DEBUG, same as
# retriever.py / metadata_filter.py. Lower-frequency here (only runs during
# ingestion, not per chat request) but still noisy in production logs.
def print(*args, **kwargs):
    if settings.DEBUG:
        _builtins.print(*args, **kwargs)


class DocumentLoader:
    """
    Loads PDF documents for the RAG pipeline.

    Supports:
    1. Normal text-based PDFs
    2. Scanned/image-based PDFs using OCR
    3. Placement PDFs -- table cells are matched to their real column
       header via pdfplumber's table-grid extraction, instead of a
       flattened-text positional guess (see _extract_placement_table_text).
    """

    def __init__(self):
        self.document_path = Path(settings.DOCUMENT_PATH)

    # Course brochures are organized by course directory. Individual pages
    # do not always repeat the course name, so retain this source metadata.
    COURSE_DIRECTORIES = {
        "BTECH": "B.TECH",
        "B.TECH": "B.TECH",
        "MCA": "MCA",
        "BCA": "BCA",
        "BBA": "BBA",
        "MBA": "MBA",
        "MTECH": "M.TECH",
        "M.TECH": "M.TECH",
    }

    def _course_from_category(self, category: str):
        return self.COURSE_DIRECTORIES.get(category.upper().strip())

    # ---------------------------------------------------------
    # OCR
    # ---------------------------------------------------------

    def _ocr_page(self, page) -> str:
        """
        Convert a PDF page into an image and extract text using OCR.
        """

        try:
            # Render PDF page at higher resolution
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )

            # Convert Pixmap → PIL Image
            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            # OCR
            text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            return text.strip()

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    # ---------------------------------------------------------
    # PLACEMENT TABLE EXTRACTION (table-grid based, not positional)
    # ---------------------------------------------------------

    def _extract_placement_table_text(self, plumber_page) -> str:
        """
        Build a clean, explicitly-labeled text block from a placement
        page's table(s) using pdfplumber's table-grid extraction.

        Why this replaces positional parsing: pdfplumber reads the
        PDF's actual table grid (rows/columns as drawn), so each value
        is matched directly to its real column header (e.g. "B.Tech
        (Computer Science)") and row label (e.g. "TOTAL OFFERS") --
        there's no guessing based on "the Nth number found near some
        phrase," which breaks the moment a stray digit (a page number,
        a schedule round number, etc.) appears nearby in the flattened
        text, or the PDF's internal text order doesn't match its
        visual layout.
        """

        try:
            tables = plumber_page.extract_tables()
        except Exception as e:
            logger.error(f"[PLACEMENT TABLE] extract_tables failed: {e}")
            return ""

        if not tables:
            return ""

        lines = []

        for table in tables:

            if not table or len(table) < 2:
                continue

            header_row = [
                (cell or "").strip()
                for cell in table[0]
            ]

            # A real header row has at least one non-empty column label
            # besides the first (row-label) cell -- skip anything that
            # doesn't look like a header.
            if not any(header_row[1:]):
                continue

            for row in table[1:]:

                cleaned = [(cell or "").strip() for cell in row]

                if not cleaned or not cleaned[0]:
                    continue

                row_label = cleaned[0]

                for col_index in range(
                    1, min(len(header_row), len(cleaned))
                ):

                    column_label = header_row[col_index]
                    value = cleaned[col_index]

                    if column_label and value:

                        lines.append(
                            f"{column_label} | {row_label}: {value}"
                        )

        if not lines:
            return ""

        return (
            "STRUCTURED PLACEMENT TABLE "
            "(column-accurate, read from the PDF's actual table grid):\n"
            + "\n".join(lines)
        )

    # ---------------------------------------------------------
    # Load normal PDF
    # ---------------------------------------------------------

    def _load_pdf(self, pdf: Path) -> List[Document]:

        documents = []

        is_placement_file = "placement" in pdf.name.lower()

        plumber_document = None

        try:

            pdf_document = fitz.open(str(pdf))

            if is_placement_file:
                # Only opened for placement PDFs -- everything else
                # keeps using fitz-only extraction as before.
                plumber_document = pdfplumber.open(str(pdf))

            logger.info(
                f"[PDF] Loading: {pdf.name}"
            )

            for page_number, page in enumerate(pdf_document):

                # -----------------------------------------
                # First try normal text extraction
                # -----------------------------------------

                text = page.get_text("text").strip()

                # -----------------------------------------
                # OCR fallback
                # -----------------------------------------

                if len(text) < 50:

                    logger.info(
                        f"[OCR] Using OCR for "
                        f"{pdf.name} - Page {page_number + 1}"
                    )

                    text = self._ocr_page(page)

                # -----------------------------------------
                # Placement table: append a clean, column-
                # accurate structured block built from the
                # PDF's actual table grid, alongside the
                # normal flattened text (which still has the
                # recruiter list, MAXIMUM/MINIMUM/AVERAGE
                # PACKAGE lines, etc. -- those are fine as
                # plain text since each is a single clearly
                # labeled number, not an ordered list of 8).
                # -----------------------------------------

                if is_placement_file and plumber_document:

                    if page_number < len(plumber_document.pages):

                        structured_table_text = (
                            self._extract_placement_table_text(
                                plumber_document.pages[page_number]
                            )
                        )

                        if structured_table_text:

                            text = (
                                f"{text}\n\n{structured_table_text}"
                                if text
                                else structured_table_text
                            )

                # -----------------------------------------
                # Skip completely empty pages
                # -----------------------------------------

                if not text:
                    logger.warning(
                        f"[EMPTY] No text found in "
                        f"{pdf.name} - Page {page_number + 1}"
                    )
                    continue

                # -----------------------------------------
                # Metadata
                # -----------------------------------------

                category = pdf.parent.name

                metadata = {
                    "source": str(pdf),
                    "filename": pdf.name,
                    "page": page_number,
                    "page_label": str(page_number + 1),
                    "category": category,
                }

                course = self._course_from_category(category)

                if course:
                    metadata["course"] = course

                # -----------------------------------------
                # Detect document type
                # -----------------------------------------

                filename_lower = pdf.name.lower()

                # Filenames occasionally contain more than one keyword
                # (e.g. "MCA_Admission_and_Fee_Structure.pdf"). Instead of
                # a fixed elif priority order that always picked
                # Placement > Fees > Admission > Academic Calendar
                # regardless of what the filename actually leads with, pick
                # whichever keyword appears earliest in the filename.
                document_type = "general"
                topic = None
                best_position = None

                candidates = [
                    ("placement", "placement", "Placement"),
                    ("fee", "fees", "Fees"),
                    ("admission", "admission", "Admission"),
                ]

                for keyword, candidate_type, candidate_topic in candidates:

                    position = filename_lower.find(keyword)

                    if position == -1:
                        continue

                    if best_position is None or position < best_position:
                        best_position = position
                        document_type = candidate_type
                        topic = candidate_topic

                if is_academic_calendar_filename(pdf.name):

                    # Academic calendar is an unambiguous, distinct
                    # document type -- it always takes precedence over the
                    # generic keyword scan above.
                    document_type = "academic_calendar"
                    topic = "Academic Calendar"

                metadata["document_type"] = document_type

                if topic:
                    metadata["topic"] = topic
                else:
                    # No filename keyword matched at all (typo, unusual
                    # naming, or a genuinely uncategorized document). This
                    # document will still be indexed, but it won't be
                    # reachable through any topic-specific retrieval
                    # branch (Fees/Eligibility/Admission/Placement) -- it
                    # only falls back to generic similarity search.
                    # Surfacing this now, at ingestion time, is much
                    # cheaper than discovering it later as an empty
                    # "no relevant documents found" chat response.
                    logger.warning(
                        f"[UNCLASSIFIED] {pdf.name} did not match any "
                        f"topic keyword (placement/fee/admission/academic "
                        f"calendar) in its filename -- indexed as "
                        f"document_type='general' with no topic. If this "
                        f"file should belong to a specific topic, check "
                        f"the filename for typos or rename it to include "
                        f"the expected keyword."
                    )

                # -----------------------------------------
                # Academic calendar metadata
                #
                # Previously hardcoded to "SP-2026"/"MO-2026" only, which
                # required a code change every academic year. Generalized
                # to match the same SP/MO-<year> naming convention for any
                # year.
                # -----------------------------------------

                semester_match = re.search(
                    r"(SP|MO)-?(\d{4})",
                    pdf.name.upper()
                )

                if semester_match:

                    semester_code, semester_year = semester_match.groups()

                    metadata["year"] = int(semester_year)

                    metadata["semester"] = (
                        "Spring" if semester_code == "SP" else "Monsoon"
                    )

                # -----------------------------------------
                # Create LangChain Document
                # -----------------------------------------

                documents.append(
                    Document(
                        page_content=text,
                        metadata=metadata
                    )
                )

            pdf_document.close()

            if plumber_document:
                plumber_document.close()

            logger.info(
                f"[SUCCESS] {pdf.name} -> "
                f"{len(documents)} document(s)"
            )

        except Exception as e:

            logger.error(
                f"[ERROR] Failed loading "
                f"{pdf.name}: {e}"
            )

        return documents

    # ---------------------------------------------------------
    # Main loader
    # ---------------------------------------------------------

    def load_documents(self) -> List[Document]:

        documents = []

        pdf_files = list(
            self.document_path.rglob("*.pdf")
        )

        print("\n========== ALL PDF FILES ==========")

        for pdf in pdf_files:
            print("FOUND PDF:", pdf)


        if not pdf_files:

            logger.warning(
                "No PDF files found."
            )

            return documents

        logger.info(
            "\n========== DOCUMENT LOADING =========="
        )

        for pdf in pdf_files:

            docs = self._load_pdf(pdf)

            documents.extend(docs)

        logger.info(
            f"\n[TOTAL] Documents/pages loaded: "
            f"{len(documents)}"
        )

        return documents