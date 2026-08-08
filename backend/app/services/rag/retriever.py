"""Document retrieval service."""

from langchain_community.vectorstores import FAISS
from streamlit import context

from app.services.rag.embedding_service import EmbeddingService
from app.services.ai.query_analyzer import QueryAnalyzer
from app.services.ai.metadata_filter import MetadataFilter
from app.services.knowledge.knowledge_manager import KnowledgeManager
from app.services.ai.context_builder import ContextBuilder


class RetrieverService:
    """
    Loads the FAISS index and retrieves
    relevant chunks.
    """

    def __init__(self):

        self.embedding_service = EmbeddingService()

        self.embeddings = self.embedding_service.get_embeddings()

        self.db = FAISS.load_local(
            "data/vector_store",
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        self.query_analyzer = QueryAnalyzer()
        self.metadata_filter = MetadataFilter()
        self.knowledge_manager = KnowledgeManager()
        self.context_builder = ContextBuilder()

    def search(self, query: str, k: int = 30):

    # -----------------------------------------
    # 1. Analyze query
    # -----------------------------------------

        analysis = self.query_analyzer.analyze(query)

        print("\n========== QUERY ANALYSIS ==========")
        print(analysis)

    # -----------------------------------------
    # 2. Raw FAISS retrieval
    # -----------------------------------------

        results = self.db.similarity_search(
            query,
            k=k
        )

        print("\n========== RAW FAISS RESULTS ==========")
        print("Total:", len(results))

        for i, doc in enumerate(results, start=1):

            print(f"\n--- RAW DOCUMENT {i} ---")

            print("COURSE :", repr(doc.metadata.get("course")))
            print("TOPIC  :", repr(doc.metadata.get("topic")))
            print("YEAR   :", repr(doc.metadata.get("year")))
            print("FILE   :", repr(doc.metadata.get("filename")))
            print("SECTION:", repr(doc.metadata.get("section")))
            print("CHUNK  :", repr(doc.metadata.get("chunk_id")))

            print("TEXT:")
            print(doc.page_content[:500])

    # -----------------------------------------
    # 3. Metadata filtering
    # -----------------------------------------

        filtered = self.metadata_filter.filter_results(
            results,
            analysis
        )

        print("\n========== AFTER METADATA FILTER ==========")
        print("Filtered:", len(filtered))

        for i, doc in enumerate(filtered, start=1):

            print(f"\n--- FILTERED DOCUMENT {i} ---")

            print("COURSE :", repr(doc.metadata.get("course")))
            print("TOPIC  :", repr(doc.metadata.get("topic")))
            print("YEAR   :", repr(doc.metadata.get("year")))
            print("FILE   :", repr(doc.metadata.get("filename")))
            print("SECTION:", repr(doc.metadata.get("section")))

    # -----------------------------------------
    # 4. Context
    # -----------------------------------------

        context = self.context_builder.build_context(filtered)

        print("\n========== CONTEXT ==========")
        print(context[:3000])

    # -----------------------------------------
    # IMPORTANT
    # -----------------------------------------

        return {
            "analysis": analysis,
            "documents": filtered,
            "context": context
        }