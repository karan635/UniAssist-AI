import uuid
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.core.config import settings
from app.services.rag.document_loader import DocumentLoader
from app.services.rag.chunk_service import ChunkService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import VectorStoreService
from app.services.rag.retriever import RetrieverService
from app.services.rag.section_splitter import SectionSplitter
from app.services.rag.index_state import (
    hash_file,
    load_manifest,
    save_manifest,
)


class IndexManager:
    """
    Central manager for the complete RAG indexing pipeline.

    Pipeline:

        PDFs
          ↓
        Document Loader
          ↓
        Metadata
          ↓
        Section Splitter
          ↓
        Chunking
          ↓
        Embeddings
          ↓
        FAISS Vector Store
          ↓
        Retriever
    """

    def __init__(self):

        # -----------------------------------------
        # Core services
        # -----------------------------------------

        self.document_loader = DocumentLoader()
        self.section_splitter = SectionSplitter()
        self.embedding_service = EmbeddingService()
        self.chunk_service = ChunkService()
        self.vector_store = VectorStoreService()

        # -----------------------------------------
        # Runtime data
        # -----------------------------------------

        self.documents: List[Document] = []
        self.chunks: List[Document] = []

        self.embeddings = None
        self.db = None
        self.retriever: Optional[RetrieverService] = None

        # -----------------------------------------
        # Incremental-indexing manifest
        # (see index_state.py)
        # -----------------------------------------

        self.manifest_path = (
            Path(settings.VECTOR_PATH) / "manifest.json"
        )

    # =========================================================
    # DOCUMENT LOADING
    # =========================================================

    def load_documents(
        self,
        force: bool = False
    ) -> List[Document]:

        if self.documents and not force:
            return self.documents

        print("\n========== DOCUMENT LOADING ==========")

        self.documents = self.document_loader.load_documents()

        print(
            f"Total documents/pages loaded: "
            f"{len(self.documents)}"
        )

        return self.documents

    # =========================================================
    # CHUNK BUILDING
    # =========================================================

    def build_chunks(
        self,
        force: bool = False
    ) -> List[Document]:

        """
        Build sections and chunks from loaded documents.
        """

        if self.chunks and not force:
            return self.chunks

        documents = self.load_documents()

        all_sections = []

        for document in documents:

            sections = self.section_splitter.split_document(
                document
            )

            all_sections.extend(sections)

        print(
            f"Total sections after section splitting: "
            f"{len(all_sections)}"
        )

        # -----------------------------------------
        # Create chunks
        # -----------------------------------------

        self.chunks = self.chunk_service.split_documents(
            all_sections
        )

        print(
            f"Total chunks after chunking: "
            f"{len(self.chunks)}"
        )

        return self.chunks

    # =========================================================
    # EMBEDDINGS
    # =========================================================

    def load_embeddings(
        self,
        force: bool = False
    ):

        if self.embeddings is not None and not force:
            return self.embeddings

        print("\n========== EMBEDDING MODEL ==========")

        self.embeddings = (
            self.embedding_service.get_embeddings()
        )

        print(
            "Embedding model loaded successfully."
        )

        return self.embeddings

    # =========================================================
    # BUILD VECTOR STORE (full, from scratch)
    # =========================================================

    def build_vector_store(
        self,
        force: bool = False
    ):

        if force:
            self.db = None
            self.retriever = None

        # -----------------------------------------
        # Make sure chunks exist
        # -----------------------------------------

        if not self.chunks:
            self.build_chunks()

        if not self.chunks:
            raise ValueError(
                "No chunks available to build FAISS vector store."
            )

        # -----------------------------------------
        # Make sure embeddings exist
        # -----------------------------------------

        if self.embeddings is None:
            self.load_embeddings()

        print("\n========== VECTOR STORE ==========")

        print(
            f"Creating FAISS index from "
            f"{len(self.chunks)} chunks..."
        )

        # Assign our own chunk IDs (instead of letting FAISS
        # auto-generate them) so they can be recorded in the manifest
        # below and later used to delete just one file's chunks if it
        # changes or is removed, without rebuilding everything.
        ids = [
            str(uuid.uuid4()) for _ in self.chunks
        ]

        self.db = self.vector_store.build(
            self.chunks,
            self.embeddings,
            ids=ids,
        )

        print(
            "FAISS vector store built successfully."
        )

        # -----------------------------------------
        # Write the indexing manifest so future
        # /index/rebuild calls can sync incrementally
        # instead of reprocessing everything again.
        # -----------------------------------------

        self._write_manifest_from_chunks(
            self.chunks,
            ids
        )

        # New index requires new retriever
        self.retriever = None

        return self.db

    def _write_manifest_from_chunks(
        self,
        chunks: List[Document],
        ids: List[str],
    ) -> None:
        """
        Group chunk IDs by the source PDF they came from, hash each
        source file, and save that as the manifest -- this is what lets
        sync() later tell which files have/haven't changed.
        """

        files: dict = {}

        for chunk, chunk_id in zip(chunks, ids):

            source = chunk.metadata.get("source")

            if not source:
                continue

            if source not in files:

                files[source] = {
                    "hash": hash_file(Path(source)),
                    "chunk_ids": [],
                }

            files[source]["chunk_ids"].append(chunk_id)

        save_manifest(
            self.manifest_path,
            {"files": files}
        )

        print(
            f"[MANIFEST] Saved indexing manifest for "
            f"{len(files)} file(s)."
        )

    # =========================================================
    # RETRIEVER
    # =========================================================

    def get_retriever(self) -> RetrieverService:

        if self.retriever is None:

            print(
                "\n========== INITIALIZING RETRIEVER =========="
            )

            # If this IndexManager already built (or loaded) a FAISS index
            # and embeddings in memory, hand them to the RetrieverService
            # directly instead of making it reload the embedding model and
            # re-deserialize the index from disk. Falls back to
            # RetrieverService's own disk-loading behavior when this
            # IndexManager hasn't built anything yet (e.g. the process was
            # just restarted and the index already exists on disk from a
            # previous run).
            self.retriever = RetrieverService(
                db=self.db,
                embeddings=self.embeddings,
            )

        return self.retriever

    # =========================================================
    # SEARCH
    # =========================================================

    def search(self, query: str, language: str = None):

        if not query or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        retriever = self.get_retriever()

        return retriever.search(
            query.strip(),
            #language=language
        )

    # =========================================================
    # COMPLETE REBUILD (full, from scratch)
    # =========================================================

    def rebuild(self):

        print("\n")
        print("=" * 60)
        print("STARTING COMPLETE RAG REBUILD")
        print("=" * 60)

        # -----------------------------------------
        # Reset runtime state
        # -----------------------------------------

        self.documents = []
        self.chunks = []
        self.embeddings = None
        self.db = None
        self.retriever = None

        # -----------------------------------------
        # STEP 1
        # Load documents
        # -----------------------------------------

        self.load_documents(force=True)

        # -----------------------------------------
        # STEP 2
        # Build chunks
        # -----------------------------------------

        self.build_chunks(force=True)

        # -----------------------------------------
        # STEP 3
        # Load embeddings
        # -----------------------------------------

        self.load_embeddings(force=True)

        # -----------------------------------------
        # STEP 4
        # Build FAISS
        # -----------------------------------------

        self.build_vector_store(force=True)

        # -----------------------------------------
        # COMPLETE
        # -----------------------------------------

        print("\n")
        print("=" * 60)
        print("RAG REBUILD COMPLETED")
        print("=" * 60)

        print(
            f"Documents : {len(self.documents)}"
        )

        print(
            f"Chunks    : {len(self.chunks)}"
        )

        return {
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "status": "success"
        }

    # =========================================================
    # INCREMENTAL SYNC
    #
    # Only new or changed PDFs get (re)chunked and (re)embedded.
    # Unchanged files are skipped entirely. Deleted files have their
    # old chunks removed from the index. Falls back to a full
    # rebuild() automatically the very first time this runs (no
    # existing index/manifest yet -- nothing to patch).
    # =========================================================

    def sync(self):

        print("\n")
        print("=" * 60)
        print("STARTING INCREMENTAL INDEX SYNC")
        print("=" * 60)

        if not self.vector_store.exists():

            print(
                "No existing FAISS index found on disk -- "
                "performing a full build instead."
            )

            return self.rebuild()

        manifest = load_manifest(self.manifest_path)
        known_files = manifest["files"]

        pdf_paths = list(
            self.document_loader.document_path.rglob("*.pdf")
        )

        current_paths = {
            str(p) for p in pdf_paths
        }

        known_paths = set(known_files.keys())

        new_paths = current_paths - known_paths
        removed_paths = known_paths - current_paths
        still_present_paths = current_paths & known_paths

        changed_paths = set()
        unchanged_paths = set()

        for path_str in still_present_paths:

            current_hash = hash_file(Path(path_str))

            if current_hash != known_files[path_str].get("hash"):
                changed_paths.add(path_str)
            else:
                unchanged_paths.add(path_str)

        print(f"New files       : {len(new_paths)}")
        print(f"Changed files   : {len(changed_paths)}")
        print(f"Removed files   : {len(removed_paths)}")
        print(f"Unchanged files : {len(unchanged_paths)}")

        if not new_paths and not changed_paths and not removed_paths:

            print("Index is already up to date. Nothing to do.")

            self.retriever = None

            return {
                "status": "success",
                "new": 0,
                "changed": 0,
                "removed": 0,
                "unchanged": len(unchanged_paths),
            }

        self.load_embeddings(force=False)

        db = self.vector_store.load(self.embeddings)

        # -----------------------------------------
        # Removed files: delete their old chunks
        # -----------------------------------------

        for path_str in removed_paths:

            old_ids = known_files.get(
                path_str, {}
            ).get("chunk_ids", [])

            db = self.vector_store.delete(db, old_ids)

            del known_files[path_str]

        # -----------------------------------------
        # Changed files: delete their old chunks
        # first, then reprocess below like a new file
        # -----------------------------------------

        for path_str in changed_paths:

            old_ids = known_files.get(
                path_str, {}
            ).get("chunk_ids", [])

            db = self.vector_store.delete(db, old_ids)

        # -----------------------------------------
        # New + changed files: chunk, embed, add
        # -----------------------------------------

        to_process = new_paths | changed_paths

        for path_str in to_process:

            pdf_path = Path(path_str)

            print(f"\n[SYNC] Processing: {pdf_path.name}")

            # DocumentLoader._load_pdf() is the same single-file loader
            # used internally by load_documents() -- reused here so a
            # sync produces identically-tagged metadata to a full
            # rebuild.
            docs = self.document_loader._load_pdf(pdf_path)

            sections = []

            for doc in docs:

                sections.extend(
                    self.section_splitter.split_document(doc)
                )

            chunks = self.chunk_service.split_documents(sections)

            ids: List[str] = []

            if chunks:

                ids = [
                    str(uuid.uuid4()) for _ in chunks
                ]

                db = self.vector_store.add(db, chunks, ids)

            known_files[path_str] = {
                "hash": hash_file(pdf_path),
                "chunk_ids": ids,
            }

            print(
                f"[SYNC] {pdf_path.name} -> "
                f"{len(chunks)} chunk(s)"
            )

        save_manifest(
            self.manifest_path,
            {"files": known_files}
        )

        self.db = db
        self.retriever = None

        print("\n")
        print("=" * 60)
        print("INCREMENTAL INDEX SYNC COMPLETED")
        print("=" * 60)

        return {
            "status": "success",
            "new": len(new_paths),
            "changed": len(changed_paths),
            "removed": len(removed_paths),
            "unchanged": len(unchanged_paths),
        }

    # =========================================================
    # DOCUMENT ACCESS
    # =========================================================

    def get_documents(
        self
    ) -> List[Document]:

        if not self.documents:
            self.load_documents()

        return self.documents

    # =========================================================
    # CHUNK ACCESS
    # =========================================================

    def get_chunks(
        self
    ) -> List[Document]:

        if not self.chunks:
            self.build_chunks()

        return self.chunks