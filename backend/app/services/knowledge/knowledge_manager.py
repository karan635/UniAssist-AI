from typing import List

from langchain_core.documents import Document

from app.services.knowledge.pdf_loader import PDFLoaderService
from app.services.knowledge.registry_builder import RegistryBuilder


class KnowledgeManager:
    """
    Central manager for the knowledge base.
    """

    def __init__(self):

        self.loader = PDFLoaderService()
        self.registry_builder = RegistryBuilder()

        self._documents: List[Document] = []
        self._registry = {}

    def load_documents(self) -> List[Document]:
        """
        Load all documents.
        """

        self._documents = self.loader.load_documents()

        return self._documents

    def build_registry(self) -> dict:
        """
        Build document registry.
        """

        self._registry = self.registry_builder.build()

        return self._registry

    def get_documents(self) -> List[Document]:
        """
        Return loaded documents.
        """

        return self._documents

    def get_registry(self) -> dict:
        """
        Return registry.
        """

        return self._registry