"""Vector store access layer."""

from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import settings


class VectorStoreService:
    """
    Handles creation, loading, and incremental updates
    of the FAISS vector database.
    """

    def __init__(self):

        self.vector_path = Path(settings.VECTOR_PATH)

        self.vector_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def exists(self) -> bool:
        """
        True if a FAISS index has already been saved to disk.

        Used to decide whether an incremental sync can proceed (load the
        existing index and patch it) or whether this has to be a first-
        time full build instead (nothing to load/patch yet).
        """

        return (
            self.vector_path / "index.faiss"
        ).exists()

    def build(
        self,
        documents: list[Document],
        embeddings,
        ids: Optional[List[str]] = None,
    ):
        """
        Build a brand new FAISS index from scratch.

        `ids` lets the caller assign its own vector IDs (instead of
        FAISS auto-generating them) so they can be recorded in the
        indexing manifest and later used to delete just this file's
        chunks if the file changes or is removed.
        """

        db = FAISS.from_documents(
            documents,
            embeddings,
            ids=ids,
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

    def add(
        self,
        db,
        documents: List[Document],
        ids: List[str],
    ):
        """
        Add new chunks to an already-loaded FAISS index in place
        (rather than rebuilding the whole index from scratch), then
        persist the updated index to disk.
        """

        db.add_documents(
            documents,
            ids=ids,
        )

        db.save_local(
            str(self.vector_path)
        )

        return db

    def delete(
        self,
        db,
        ids: List[str],
    ):
        """
        Remove specific chunks from an already-loaded FAISS index by
        their vector IDs (e.g. a file's old chunks, before re-adding
        its updated ones, or a file that was deleted entirely), then
        persist the updated index to disk.
        """

        if ids:
            db.delete(ids)
            db.save_local(str(self.vector_path))

        return db