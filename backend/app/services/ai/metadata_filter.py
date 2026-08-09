from langchain_core.documents import Document


class MetadataFilter:

    # =========================================================
    # COURSE NORMALIZATION
    # =========================================================

    def normalize_course(self, course):

        if not course:
            return None

        course = str(course).upper().strip()

        replacements = {

            # B.Tech
            "BTECH": "B.TECH",
            "B.TECH.": "B.TECH",
            "B.TECH": "B.TECH",

            # MCA
            "MCA": "MCA",

            # BCA
            "BCA": "BCA",

            # BBA
            "BBA": "BBA",

            # MBA
            "MBA": "MBA",

            # M.Sc
            "MSC": "M.SC",
            "M.SC.": "M.SC",
            "M.SC": "M.SC",

            # B.Sc
            "BSC": "B.SC",
            "B.SC.": "B.SC",
            "B.SC": "B.SC",

            # M.Pharm
            "MPHARM": "M.PHARM",
            "M.PHARM.": "M.PHARM",
            "M.PHARM": "M.PHARM",

            # B.Pharm
            "BPHARM": "B.PHARM",
            "B.PHARM.": "B.PHARM",
            "B.PHARM": "B.PHARM",

            # M.Tech
            "MTECH": "M.TECH",
            "M.TECH.": "M.TECH",
            "M.TECH": "M.TECH",

            # B.Arch
            "BARCH": "B.ARCH",
            "B.ARCH.": "B.ARCH",
            "B.ARCH": "B.ARCH",

            # Academic groups
            "UG": "UG",
            "PG": "PG",
            "PHD": "PHD",
            "PH.D": "PHD",
            "PH.D.": "PHD",
        }

        return replacements.get(
            course,
            course
        )

    # =========================================================
    # ACADEMIC GROUP
    # =========================================================

    def course_to_academic_group(self, course):

        course = self.normalize_course(course)

        if not course:
            return None

        # -----------------------------------------------------
        # Undergraduate
        # -----------------------------------------------------

        if course in {
            "B.TECH",
            "BCA",
            "BBA",
            "B.ARCH",
            "B.PHARM",
            "B.SC",
        }:
            return "UG"

        # -----------------------------------------------------
        # Postgraduate
        # -----------------------------------------------------

        if course in {
            "MCA",
            "MBA",
            "M.PHARM",
            "M.TECH",
            "M.SC",
        }:
            return "PG"

        # -----------------------------------------------------
        # PhD
        # -----------------------------------------------------

        if course == "PHD":
            return "PHD"

        return None

    # =========================================================
    # TOPIC NORMALIZATION
    # =========================================================

    def normalize_topic(self, topic):

        if not topic:
            return None

        topic = str(topic).strip().lower()

        mapping = {

            "fee": "Fees",
            "fees": "Fees",

            "eligibility": "Eligibility",

            "admission": "Admission",

            "placement": "Placement",
            "placements": "Placement",

            "academic calendar": "Academic Calendar",
            "academic calendars": "Academic Calendar",
            "calendar": "Academic Calendar",
        }

        return mapping.get(
            topic,
            topic.title()
        )

    # =========================================================
    # TOPIC MATCHING
    # =========================================================

    def topic_matches(self, doc, query_topic):
        """Match metadata topics and eligibility sections in admission PDFs."""

        query_topic = self.normalize_topic(query_topic)
        document_topic = self.normalize_topic(
            doc.metadata.get("topic")
        )

        if document_topic == query_topic:
            return True

        # Eligibility criteria is commonly embedded within an admission
        # brochure, which remains tagged as Admission at the file level.
        if (
            query_topic == "Eligibility"
            and document_topic == "Admission"
        ):
            text = (
                f"{doc.page_content} "
                f"{doc.metadata.get('section', '')}"
            ).lower()

            return (
                "eligibility criteria" in text
                or "eligibility" in text
                or "eligible" in text
            )

        return False

    # =========================================================
    # ACADEMIC CALENDAR CONTENT MATCH
    # =========================================================

    def academic_calendar_content_matches(
        self,
        doc,
        query_course
    ):

        if not query_course:
            return True

        query_course = self.normalize_course(
            query_course
        )

        metadata = doc.metadata

        # -----------------------------------------------------
        # Combine searchable text
        # -----------------------------------------------------

        text = (
            str(doc.page_content)
            + " "
            + str(metadata.get("section", ""))
            + " "
            + str(metadata.get("filename", ""))
        ).upper()

        # -----------------------------------------------------
        # B.Tech
        # -----------------------------------------------------

        if query_course == "B.TECH":

            return (
                "B.TECH" in text
                or "BTECH" in text
                or "B TECH" in text
                or "ENGINEERING" in text
            )

        # -----------------------------------------------------
        # MCA
        # -----------------------------------------------------

        if query_course == "MCA":
            return "MCA" in text

        # -----------------------------------------------------
        # BCA
        # -----------------------------------------------------

        if query_course == "BCA":
            return "BCA" in text

        # -----------------------------------------------------
        # BBA
        # -----------------------------------------------------

        if query_course == "BBA":
            return "BBA" in text

        # -----------------------------------------------------
        # MBA
        # -----------------------------------------------------

        if query_course == "MBA":
            return "MBA" in text

        # -----------------------------------------------------
        # B.Sc
        # -----------------------------------------------------

        if query_course == "B.SC":
            return (
                "B.SC" in text
                or "BSC" in text
                or "BACHELOR OF SCIENCE" in text
            )

        # -----------------------------------------------------
        # M.Sc
        # -----------------------------------------------------

        if query_course == "M.SC":
            return (
                "M.SC" in text
                or "MSC" in text
                or "MASTER OF SCIENCE" in text
            )

        return False

    # =========================================================
    # COURSE MATCHING
    # =========================================================

    def course_matches(
        self,
        doc,
        query_course
    ):

        # No course requested
        if not query_course:
            return True

        query_course = self.normalize_course(
            query_course
        )

        metadata = doc.metadata

        # =====================================================
        # DOCUMENT COURSE
        # =====================================================

        doc_course = self.normalize_course(
            metadata.get("course")
        )

        # Older indexed chunks predate the explicit `course` metadata. Their
        # course directory is still preserved as `category`.
        category_course = self.normalize_course(
            metadata.get("category")
        )

        # =====================================================
        # MULTIPLE COURSES
        # =====================================================

        doc_courses = metadata.get(
            "courses",
            []
        )

        if not isinstance(
            doc_courses,
            list
        ):
            doc_courses = [
                doc_courses
            ]

        doc_courses = [
            self.normalize_course(course)
            for course in doc_courses
            if course
        ]

        # =====================================================
        # DIRECT COURSE MATCH
        # =====================================================

        if doc_course:

            if doc_course == query_course:
                return True

        # Use category only for legacy chunks with no section-level course.
        if not doc_course and category_course == query_course:
            return True

        # =====================================================
        # MULTIPLE COURSE MATCH
        # =====================================================

        if query_course in doc_courses:
            return True

        # =====================================================
        # DOCUMENT TYPE
        # =====================================================

        document_type = str(
            metadata.get(
                "document_type",
                ""
            )
        ).lower().strip()

        topic = self.normalize_topic(
            metadata.get("topic")
        )

        # =====================================================
        # ACADEMIC CALENDAR
        # =====================================================

        if (
            document_type == "academic_calendar"
            or topic == "Academic Calendar"
        ):

            # -------------------------------------------------
            # First check calendar_group
            # -------------------------------------------------

            calendar_group = self.normalize_course(
                metadata.get(
                    "calendar_group"
                )
            )

            expected_group = (
                self.course_to_academic_group(
                    query_course
                )
            )

            if (
                calendar_group
                and expected_group
            ):

                if calendar_group == expected_group:
                    return True

                # If explicitly another group,
                # don't accept it.
                return False

            # -------------------------------------------------
            # If metadata does not tell us the group,
            # inspect the actual document.
            # -------------------------------------------------

            return self.academic_calendar_content_matches(
                doc,
                query_course
            )

        # =====================================================
        # PLACEMENT DOCUMENT
        # =====================================================

        if document_type == "placement":

            # Placement document has one course
            if doc_course:

                return (
                    doc_course == query_course
                )

            # Placement document has multiple courses
            if doc_courses:

                return (
                    query_course in doc_courses
                )

            return False

        # =====================================================
        # NORMAL DOCUMENTS
        # =====================================================

        if doc_course:

            return (
                doc_course == query_course
            )

        if doc_courses:

            return (
                query_course in doc_courses
            )

        return False

    # =========================================================
    # FILTER RESULTS
    # =========================================================

    def filter_results(
        self,
        results,
        analysis
    ):

        filtered = []

        # =====================================================
        # QUERY INFORMATION
        # =====================================================

        query_course = self.normalize_course(
            analysis.get("course")
        )

        query_topic = self.normalize_topic(
            analysis.get("topic")
        )

        query_year = analysis.get(
            "year"
        )

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

        # =====================================================
        # LOOP THROUGH RESULTS
        # =====================================================

        for doc in results:

            metadata = doc.metadata

            doc_course = self.normalize_course(
                metadata.get("course")
            )

            doc_courses = metadata.get(
                "courses",
                []
            )

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
                if c
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
            ).lower().strip()

            # =================================================
            # DEBUG
            # =================================================

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
            # TOPIC FILTER
            # =================================================

            if query_topic and not self.topic_matches(
                doc,
                query_topic
            ):

                continue

            # =================================================
            # YEAR FILTER
            # =================================================

            if query_year:

                if doc_year is not None:

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

                    # If query specifies a year,
                    # document must have a year.
                    continue

            # =================================================
            # COURSE FILTER
            # =================================================

            if query_course:

                if not self.course_matches(
                    doc,
                    query_course
                ):

                    continue

            # =================================================
            # ADD DOCUMENT
            # =================================================

            filtered.append(
                doc
            )

        # =====================================================
        # RESULT
        # =====================================================

        print(
            "Filtered Results:",
            len(filtered)
        )

        return filtered
