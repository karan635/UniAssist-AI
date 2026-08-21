"""Document ingestion utilities for the RAG pipeline."""

from pathlib import Path
from typing import List

import os
import platform
import re
import shutil

import fitz  # PyMuPDF
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
    # Load normal PDF
    # ---------------------------------------------------------

    def _load_pdf(self, pdf: Path) -> List[Document]:

        documents = []

        try:

            pdf_document = fitz.open(str(pdf))

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