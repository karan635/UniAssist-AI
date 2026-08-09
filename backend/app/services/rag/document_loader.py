"""Document ingestion utilities for the RAG pipeline."""

from pathlib import Path
from typing import List

import fitz  # PyMuPDF
import pytesseract

from PIL import Image
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logger import logger


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

                if "placement" in filename_lower:

                    metadata["document_type"] = "placement"
                    metadata["topic"] = "Placement"

                elif "fee" in filename_lower:

                    metadata["document_type"] = "fees"
                    metadata["topic"] = "Fees"

                elif "admission" in filename_lower:

                    metadata["document_type"] = "admission"
                    metadata["topic"] = "Admission"

                elif ("academiccalendar" in filename_lower or "academic calendars" in filename_lower):

                    metadata["document_type"] = "academic_calendar"
                    metadata["topic"] = "Academic Calendar"

                else:

                    metadata["document_type"] = "general"

                # -----------------------------------------
                # Academic calendar metadata
                # -----------------------------------------

                if "SP-2026" in pdf.name.upper():

                    metadata["year"] = 2026
                    metadata["semester"] = "Spring"

                elif "MO-2026" in pdf.name.upper():

                    metadata["year"] = 2026
                    metadata["semester"] = "Monsoon"

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
