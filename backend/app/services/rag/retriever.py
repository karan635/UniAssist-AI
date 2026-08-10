"""Document retrieval service."""

from langchain_community.vectorstores import FAISS

from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.services.ai.query_analyzer import QueryAnalyzer
from app.services.ai.metadata_filter import MetadataFilter
from app.services.knowledge.knowledge_manager import KnowledgeManager
from app.services.ai.context_builder import ContextBuilder
from app.utils.text_matching import is_academic_calendar_filename

# This module traces every retrieval step (full query analysis, the entire
# FAISS docstore, up to 1000 chars of every candidate document) with bare
# print() calls, unconditionally, on every request. That's genuinely useful
# during local debugging but floods production logs and adds real
# per-request overhead when left on. Rather than touching every one of the
# ~50 call sites below (and risking breaking one), shadow `print` at module
# scope so all of that existing debug output is gated behind settings.DEBUG
# without changing what gets printed or how.
import builtins as _builtins


def print(*args, **kwargs):
    if settings.DEBUG:
        _builtins.print(*args, **kwargs)


class RetrieverService:
    """
    Loads the FAISS index and retrieves
    relevant chunks.
    """

    def __init__(self, db=None, embeddings=None):

        # Allow a caller that already has a loaded FAISS index and
        # embedding model in memory (e.g. IndexManager right after
        # build_vector_store()) to pass them in directly, instead of this
        # constructor always re-loading the embedding model and
        # re-deserializing the FAISS index from disk from scratch. Passing
        # nothing preserves the previous standalone behavior.
        if embeddings is not None:
            self.embeddings = embeddings
        else:
            self.embedding_service = EmbeddingService()
            self.embeddings = self.embedding_service.get_embeddings()

        if db is not None:
            self.db = db
        else:
            self.db = FAISS.load_local(
                settings.VECTOR_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )

        self.query_analyzer = QueryAnalyzer()

        self.metadata_filter = MetadataFilter()

        self.knowledge_manager = KnowledgeManager()

        self.context_builder = ContextBuilder()


    # =================================================
    # EXPAND RELATED CHUNKS
    # =================================================

    def _expand_related_chunks(
        self,
        documents,
        all_documents,
        max_following: int = 2,
    ):
        """
        Include continuation chunks from the same logical
        document/section.

        Eligibility criteria can continue into the next chunk.
        We therefore match by source + chunk-id family rather
        than relying only on the global chunk_number.
        """

        if not documents:
            return documents

        expanded = list(documents)

        for document in list(documents):

            metadata = document.metadata

            source = metadata.get("filename")
            course = metadata.get("course")
            current_chunk_id = str(
                metadata.get("chunk_id", "")
            )

            current_chunk_number = metadata.get(
                "chunk_number"
            )

            # -------------------------------------------------
            # Determine the logical chunk family.
            #
            # Example:
            # MCA_Admission__13
            # MCA_Admission__14
            #
            # Both belong to the same MCA Admission sequence.
            # -------------------------------------------------

            chunk_prefix = None

            if "__" in current_chunk_id:
                chunk_prefix = current_chunk_id.rsplit(
                    "__",
                    1
                )[0]

            try:
                current_number = int(
                    current_chunk_number
                )
            except (TypeError, ValueError):
                current_number = None

            candidates = []

            for candidate in all_documents:

                if candidate is document:
                    continue

                candidate_metadata = candidate.metadata

                # -------------------------------------------------
                # Same source PDF
                # -------------------------------------------------

                if (
                    source
                    and candidate_metadata.get("filename")
                    != source
                ):
                    continue

                candidate_chunk_id = str(
                    candidate_metadata.get(
                        "chunk_id",
                        ""
                    )
                )

                # -------------------------------------------------
                # Prefer the same chunk-id family.
                # -------------------------------------------------

                if chunk_prefix:

                    if not candidate_chunk_id.startswith(
                        chunk_prefix + "__"
                    ):
                        continue

                else:

                    # Fallback when chunk_id is unavailable.
                    candidate_course = (
                        candidate_metadata.get("course")
                    )

                    if (
                        course
                        and candidate_course
                        and candidate_course != course
                    ):
                        continue

                candidate_number = (
                    candidate_metadata.get(
                        "chunk_number"
                    )
                )

                try:
                    candidate_number = int(
                        candidate_number
                    )
                except (TypeError, ValueError):
                    continue

                # Only following chunks.
                if (
                    current_number is not None
                    and candidate_number <= current_number
                ):
                    continue

                candidates.append(
                    candidate
                )

            # -------------------------------------------------
            # Sort continuation chunks.
            # -------------------------------------------------

            candidates.sort(
                key=lambda doc: int(
                    doc.metadata.get(
                        "chunk_number",
                        999999
                    )
                )
            )

            print(
                "\n========== CHUNK EXPANSION DEBUG =========="
            )

            print(
                "Current chunk:",
                current_chunk_id
            )

            print(
                "Source:",
                source
            )

            print(
                "Course:",
                course
            )

            print(
                "Continuation candidates:",
                [
                    (
                        doc.metadata.get("chunk_id"),
                        doc.metadata.get("chunk_number")
                    )
                    for doc in candidates
                ]
            )

            # -------------------------------------------------
            # Add only the next N chunks.
            # -------------------------------------------------

            for candidate in candidates[
                :max_following
            ]:

                if candidate not in expanded:

                    expanded.append(
                        candidate
                    )

                    print(
                        "[CHUNK EXPANSION] Added:",
                        candidate.metadata.get(
                            "chunk_id"
                        )
                    )

        return expanded

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
                    or is_academic_calendar_filename(filename)
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
                    or is_academic_calendar_filename(filename)
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

                if not self.metadata_filter.topic_matches(
                    doc,
                    topic
                ):

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

            # -------------------------------------------------
            # Eligibility can span multiple chunks.
            # Include following chunks from the same source/course.
            # -------------------------------------------------

            if topic == "Eligibility" and filtered:

                filtered = self._expand_related_chunks(
                    filtered,
                    all_documents,
                    max_following=2,
                )

                print(
                    "Eligibility candidates after chunk expansion:",
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