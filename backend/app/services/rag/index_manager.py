from typing import List, Optional

from langchain_core.documents import Document

from app.services.rag.document_loader import DocumentLoader
from app.services.rag.chunk_service import ChunkService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import VectorStoreService
from app.services.rag.retriever import RetrieverService
from app.services.rag.section_splitter import SectionSplitter


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
    # BUILD VECTOR STORE
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

        self.db = self.vector_store.build(
            self.chunks,
            self.embeddings
        )

        print(
            "FAISS vector store built successfully."
        )

        # New index requires new retriever
        self.retriever = None

        return self.db

    # =========================================================
    # RETRIEVER
    # =========================================================

    def get_retriever(self) -> RetrieverService:

        if self.retriever is None:

            print(
                "\n========== INITIALIZING RETRIEVER =========="
            )

            self.retriever = RetrieverService()

        return self.retriever

    # =========================================================
    # SEARCH
    # =========================================================

    def search(self, query: str):

        if not query or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        retriever = self.get_retriever()

        return retriever.search(
            query.strip()
        )

    # =========================================================
    # COMPLETE REBUILD
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