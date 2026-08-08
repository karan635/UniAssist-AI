"""Vector store access layer."""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class VectorStoreService:
    """
    Handles creation and loading
    of the FAISS vector database.
    """

    def __init__(self):

        self.vector_path = Path("data/vector_store")

        self.vector_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def build(
        self,
        documents: list[Document],
        embeddings,
    ):

        db = FAISS.from_documents(
            documents,
            embeddings
        )

        db.save_local(
            str(self.vector_path)
        )

        return db

    def load(
        self,
        embeddings,
    ):

        return FAISS.load_local(
            str(self.vector_path),
            embeddings,
            allow_dangerous_deserialization=True
        )