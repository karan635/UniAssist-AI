"""Document ingestion utilities for the RAG pipeline."""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.config import settings
from app.core.logger import logger


class DocumentLoader:
    """
    Loads all PDF documents from the configured document directory.
    """

    def __init__(self):
        self.document_path = Path(settings.DOCUMENT_PATH)

    def load_documents(self) -> List[Document]:
        documents = []

        pdf_files = list(self.document_path.rglob("*.pdf"))

        if not pdf_files:
            logger.warning("No PDF files found.")

        for pdf in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf))
                docs = loader.load()

                # Add category metadata
                category = pdf.parent.name

                for doc in docs:
                    doc.metadata["category"] = category
                    doc.metadata["filename"] = pdf.name

                documents.extend(docs)

                logger.info(f"Loaded {pdf.name}")

            except Exception as e:
                logger.error(f"Error loading {pdf.name}: {e}")

        logger.info(f"Total pages loaded: {len(documents)}")

        return documents