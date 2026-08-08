from langchain_core.documents import Document


class MetadataFilter:

    # =========================================================
    # COURSE NORMALIZATION
    # =========================================================

    def normalize_course(self, course):

        if not course:
            return None

        course = str(
            course
        ).upper().strip()

        replacements = {

            "BTECH": "B.TECH",
            "B.TECH.": "B.TECH",
            "B.TECH": "B.TECH",

            "MCA": "MCA",

            "BCA": "BCA",

            "BBA": "BBA",

            "MBA": "MBA",

            "MSC": "M.SC",
            "M.SC.": "M.SC",
            "M.SC": "M.SC",

            "BSC": "B.SC",
            "B.SC.": "B.SC",
            "B.SC": "B.SC",

            "MPHARM": "M.PHARM",
            "M.PHARM.": "M.PHARM",
            "M.PHARM": "M.PHARM",

            "BPHARM": "B.PHARM",
            "B.PHARM.": "B.PHARM",
            "B.PHARM": "B.PHARM",

        }

        return replacements.get(
            course,
            course
        )

    # =========================================================
    # TOPIC NORMALIZATION
    # =========================================================

    def normalize_topic(self, topic):

        if not topic:
            return None

        topic = str(
            topic
        ).strip().lower()

        mapping = {

            "fee": "Fees",
            "fees": "Fees",

            "eligibility": "Eligibility",

            "admission": "Admission",

            "placement": "Placement",
            "placements": "Placement",

        }

        return mapping.get(
            topic,
            topic.title()
        )

    # =========================================================
    # FILTER
    # =========================================================

    def filter_results(
        self,
        results,
        analysis
    ):

        filtered = []

        query_course = self.normalize_course(
            analysis.get("course")
        )

        query_topic = self.normalize_topic(
            analysis.get("topic")
        )

        query_year = analysis.get("year")

        print(
            "\n========== METADATA FILTER =========="
        )

        print(
            "Query Course:",
            query_course
        )

        print(
            "Query Topic:",
            query_topic
        )

        print(
            "Query Year:",
            query_year
        )

        for doc in results:

            metadata = doc.metadata

            doc_course = self.normalize_course(
                metadata.get("course")
            )

            doc_courses = metadata.get(
                "courses",
                []
            )

            # Normalize list
            if not isinstance(
                doc_courses,
                list
            ):
                doc_courses = [
                    doc_courses
                ]

            doc_courses = [
                self.normalize_course(c)
                for c in doc_courses
            ]

            doc_topic = self.normalize_topic(
                metadata.get("topic")
            )

            doc_year = metadata.get(
                "year"
            )

            document_type = str(
                metadata.get(
                    "document_type",
                    ""
                )
            ).lower()

            print(
                "DOC:",
                metadata.get("filename"),
                "| COURSE:",
                doc_course,
                "| COURSES:",
                doc_courses,
                "| TOPIC:",
                doc_topic,
                "| YEAR:",
                doc_year,
                "| TYPE:",
                document_type
            )

            # =================================================
            # TOPIC
            # =================================================

            if query_topic:

                if doc_topic != query_topic:
                    continue

            # =================================================
            # YEAR
            # =================================================

            if query_year:

                if doc_year:

                    try:

                        if int(doc_year) != int(
                            query_year
                        ):
                            continue

                    except (
                        ValueError,
                        TypeError
                    ):
                        continue

                else:

                    # If user explicitly asked for a year
                    # and document has no year,
                    # don't use it.
                    continue

            # =================================================
            # COURSE
            # =================================================

            if query_course:

                # ---------------------------------------------
                # Normal document
                # ---------------------------------------------

                if document_type != "placement":

                    if doc_course != query_course:
                        continue

                # ---------------------------------------------
                # Placement document
                # ---------------------------------------------

                else:

                    # Single-course placement
                    if doc_course:

                        if doc_course != query_course:
                            continue

                    # Multi-course placement
                    elif doc_courses:

                        if query_course not in doc_courses:
                            continue

                    else:

                        # Unknown placement course
                        continue

            filtered.append(doc)

        print(
            "Filtered Results:",
            len(filtered)
        )

        return filtered