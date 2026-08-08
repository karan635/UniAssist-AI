"""Document retrieval service."""

from langchain_community.vectorstores import FAISS

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

        self.embeddings = (
            self.embedding_service.get_embeddings()
        )

        self.db = FAISS.load_local(
            "data/vector_store",
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        self.query_analyzer = QueryAnalyzer()

        self.metadata_filter = MetadataFilter()

        self.knowledge_manager = KnowledgeManager()

        self.context_builder = ContextBuilder()

    # =====================================================
    # SEARCH
    # =====================================================

    def search(
        self,
        query: str,
        k: int = 30
    ):

        # =================================================
        # 1. ANALYZE QUERY
        # =================================================

        analysis = self.query_analyzer.analyze(
            query
        )

        print(
            "\n========== QUERY ANALYSIS =========="
        )

        print(analysis)

        course = analysis.get(
            "course"
        )

        topic = analysis.get(
            "topic"
        )

        year = analysis.get(
            "year"
        )

        # =================================================
        # 2. NORMALIZE
        # =================================================

        if course:

            course = (
                self.metadata_filter
                .normalize_course(course)
            )

        if topic:

            topic = (
                self.metadata_filter
                .normalize_topic(topic)
            )

        print(
            "\nNormalized Course:",
            course
        )

        print(
            "Normalized Topic:",
            topic
        )

        print(
            "Year:",
            year
        )

        # =================================================
        # 3. INITIALIZE
        # =================================================

        filtered = []

        # =================================================
        # 4. DIRECT DOCUMENT STORE
        # =================================================
        #
        # FAISS keeps the original LangChain documents
        # inside its docstore.
        #
        # We use these documents for structured topics
        # instead of depending entirely on vector similarity.
        # =================================================

        all_documents = list(
            self.db.docstore._dict.values()
        )

        print(
            "\n========== FAISS DOCSTORE =========="
        )

        print(
            "Total indexed documents:",
            len(all_documents)
        )

        # =================================================
        # 5. DEBUG ACADEMIC CALENDAR DOCUMENTS
        # =================================================
        #
        # This is especially useful right now because
        # we need to know exactly what metadata was stored
        # for the calendar PDFs.
        # =================================================

        if topic == "Academic Calendar":

            print(
                "\n========== ALL ACADEMIC CALENDAR DOCUMENTS =========="
            )

            for doc in all_documents:

                metadata = doc.metadata

                filename = str(
                    metadata.get(
                        "filename",
                        ""
                    )
                )

                doc_topic = (
                    self.metadata_filter
                    .normalize_topic(
                        metadata.get("topic")
                    )
                )

                document_type = str(
                    metadata.get(
                        "document_type",
                        ""
                    )
                ).lower()

                if (
                    doc_topic == "Academic Calendar"
                    or document_type == "academic_calendar"
                    or "academiccalendar" in (
                        filename
                        .lower()
                        .replace(" ", "")
                    )
                ):

                    print(
                        "\nFILE:",
                        filename
                    )

                    print(
                        "METADATA:",
                        metadata
                    )

                    print(
                        "TEXT:",
                        doc.page_content[:500]
                    )

        # =================================================
        # 6. ACADEMIC CALENDAR
        # =================================================

        if topic == "Academic Calendar":

            print(
                "\n========== DIRECT ACADEMIC CALENDAR RETRIEVAL =========="
            )

            for doc in all_documents:

                metadata = doc.metadata

                filename = str(
                    metadata.get(
                        "filename",
                        ""
                    )
                )

                doc_topic = (
                    self.metadata_filter
                    .normalize_topic(
                        metadata.get("topic")
                    )
                )

                document_type = str(
                    metadata.get(
                        "document_type",
                        ""
                    )
                ).lower()

                doc_year = metadata.get(
                    "year"
                )

                # -----------------------------------------
                # TOPIC MATCH
                # -----------------------------------------

                topic_match = (
                    doc_topic
                    == "Academic Calendar"
                    or document_type
                    == "academic_calendar"
                    or "academiccalendar" in (
                        filename
                        .lower()
                        .replace(" ", "")
                    )
                )

                if not topic_match:

                    continue

                # -----------------------------------------
                # YEAR MATCH
                # -----------------------------------------

                if year:

                    year_match = False

                    if doc_year is not None:

                        try:

                            year_match = (
                                int(doc_year)
                                == int(year)
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            year_match = False

                    # Filename fallback

                    if not year_match:

                        year_match = (
                            str(year)
                            in filename
                        )

                    if not year_match:

                        continue

                # -----------------------------------------
                # COURSE MATCH
                # -----------------------------------------

                if course:

                    if not (
                        self.metadata_filter
                        .course_matches(
                            doc,
                            course
                        )
                    ):

                        continue

                # -----------------------------------------
                # ADD
                # -----------------------------------------

                filtered.append(
                    doc
                )

            print(
                "\nAcademic Calendar candidates:",
                len(filtered)
            )

        # =================================================
        # 7. FEES / PLACEMENT / ADMISSION / ELIGIBILITY
        # =================================================

        elif topic in {
            "Fees",
            "Placement",
            "Admission",
            "Eligibility"
        }:

            print(
                f"\n========== DIRECT {topic.upper()} RETRIEVAL =========="
            )

            for doc in all_documents:

                metadata = doc.metadata

                doc_topic = (
                    self.metadata_filter
                    .normalize_topic(
                        metadata.get("topic")
                    )
                )

                doc_year = metadata.get(
                    "year"
                )

                # -----------------------------------------
                # TOPIC
                # -----------------------------------------

                if doc_topic != topic:

                    continue

                # -----------------------------------------
                # YEAR
                # -----------------------------------------

                if year:

                    if doc_year is not None:

                        try:

                            if int(doc_year) != int(
                                year
                            ):

                                continue

                        except (
                            ValueError,
                            TypeError
                        ):

                            continue

                # -----------------------------------------
                # COURSE
                # -----------------------------------------

                if course:

                    if not (
                        self.metadata_filter
                        .course_matches(
                            doc,
                            course
                        )
                    ):

                        continue

                filtered.append(
                    doc
                )

            print(
                f"{topic} candidates:",
                len(filtered)
            )

        # =================================================
        # 8. FALLBACK TO FAISS
        # =================================================
        #
        # If direct retrieval doesn't find anything,
        # fall back to semantic search.
        # =================================================

        if not filtered:

            print(
                "\n========== FALLBACK FAISS SEARCH =========="
            )

            results = (
                self.db.similarity_search(
                    query,
                    k=k
                )
            )

            print(
                "Raw FAISS results:",
                len(results)
            )

            # Debug raw results

            for i, doc in enumerate(
                results,
                start=1
            ):

                print(
                    f"\n--- RAW DOCUMENT {i} ---"
                )

                print(
                    "COURSE:",
                    doc.metadata.get(
                        "course"
                    )
                )

                print(
                    "COURSES:",
                    doc.metadata.get(
                        "courses"
                    )
                )

                print(
                    "TOPIC:",
                    doc.metadata.get(
                        "topic"
                    )
                )

                print(
                    "YEAR:",
                    doc.metadata.get(
                        "year"
                    )
                )

                print(
                    "FILE:",
                    doc.metadata.get(
                        "filename"
                    )
                )

                print(
                    "SECTION:",
                    doc.metadata.get(
                        "section"
                    )
                )

                print(
                    "CHUNK:",
                    doc.metadata.get(
                        "chunk_id"
                    )
                )

                print(
                    "TEXT:"
                )

                print(
                    doc.page_content[:1000]
                )

            filtered = (
                self.metadata_filter
                .filter_results(
                    results,
                    analysis
                )
            )

        # =================================================
        # 9. TOPIC BASED LIMIT
        # =================================================

        topic_k = {

            "Fees": 8,

            "Eligibility": 5,

            "Admission": 6,

            "Placement": 10,

            "Academic Calendar": 8,
        }

        final_k = topic_k.get(
            topic,
            5
        )

        filtered = filtered[
            :final_k
        ]

        # =================================================
        # 10. FINAL DOCUMENT DEBUG
        # =================================================

        print(
            "\n========== FINAL RETRIEVED DOCUMENTS =========="
        )

        print(
            "Final documents:",
            len(filtered)
        )

        for i, doc in enumerate(
            filtered,
            start=1
        ):

            metadata = doc.metadata

            print(
                f"\n--- FINAL DOCUMENT {i} ---"
            )

            print(
                "FILE:",
                metadata.get(
                    "filename"
                )
            )

            print(
                "COURSE:",
                metadata.get(
                    "course"
                )
            )

            print(
                "COURSES:",
                metadata.get(
                    "courses"
                )
            )

            print(
                "CALENDAR GROUP:",
                metadata.get(
                    "calendar_group"
                )
            )

            print(
                "TOPIC:",
                metadata.get(
                    "topic"
                )
            )

            print(
                "YEAR:",
                metadata.get(
                    "year"
                )
            )

            print(
                "DOCUMENT TYPE:",
                metadata.get(
                    "document_type"
                )
            )

            print(
                "SECTION:",
                metadata.get(
                    "section"
                )
            )

            print(
                "CHUNK:",
                metadata.get(
                    "chunk_id"
                )
            )

            print(
                "TEXT:"
            )

            print(
                doc.page_content[:1000]
            )

        # =================================================
        # 11. BUILD CONTEXT
        # =================================================

        context = (
            self.context_builder
            .build_context(
                filtered
            )
        )

        print(
            "\n========== FINAL CONTEXT =========="
        )

        print(
            context
        )

        # =================================================
        # 12. RETURN
        # =================================================

        return {

            "analysis": analysis,

            "documents": filtered,

            "context": context
        }   