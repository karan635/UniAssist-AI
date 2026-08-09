import re

from langchain_core.documents import Document


class SectionSplitter:

    COURSE_PATTERNS = {
        "B.TECH": [
            r"\bB\.?\s*Tech\b",
            r"\bBTech\b",
            r"\bBachelor\s+of\s+Technology\b",
        ],
        "MCA": [
            r"\bMaster of Computer Application\b",
            r"\bMCA\b",
        ],
        "MBA": [
            r"\bMaster of Business Administration\b",
            r"\bMBA\b",
        ],
        "BCA": [
            r"\bBCA\b",
            r"\bBachelor of Computer Application\b",
        ],
        "BBA": [
            r"\bBBA\b",
            r"\bBachelor of Business Administration\b",
        ],
        "B.ARCH": [
            r"\bB\.?\s*Arch\b",
            r"\bBachelor of Architecture\b",
        ],
        "B.PHARM": [
            r"\bB\.?\s*Pharm\b",
            r"\bBachelor of Pharmacy\b",
        ],
        "M.PHARM": [
            r"\bM\.?\s*Pharm\b",
            r"\bMaster of Pharmacy\b",
        ],
        "M.TECH": [
            r"\bM\.?\s*Tech\b",
            r"\bMaster of Technology\b",
        ],
        "M.SC": [
            r"\bM\.?\s*Sc\b",
            r"\bMaster of Science\b",
        ],
        "B.SC": [
            r"\bB\.?\s*Sc\b",
            r"\bBachelor of Science\b",
        ],
    }

    # =========================================================
    # COURSE DETECTION
    # =========================================================

    def detect_courses(self, text: str):

        courses = []

        text_upper = text.upper()

        checks = {
            "B.TECH": [
                r"\bB\.?\s*TECH\b",
                r"\bBTECH\b",
                r"\bBACHELOR\s+OF\s+TECHNOLOGY\b",
            ],
            "MCA": [
                r"\bMASTER OF COMPUTER APPLICATION\b",
                r"\bMCA\b",
            ],
            "MBA": [
                r"\bMASTER OF BUSINESS ADMINISTRATION\b",
                r"\bMBA\b",
            ],
            "BCA": [
                r"\bBCA\b",
                r"\bBACHELOR OF COMPUTER APPLICATION\b",
            ],
            "BBA": [
                r"\bBBA\b",
                r"\bBACHELOR OF BUSINESS ADMINISTRATION\b",
            ],
            "B.ARCH": [
                r"\bB\.?\s*ARCH\b",
                r"\bBACHELOR OF ARCHITECTURE\b",
            ],
            "B.PHARM": [
                r"\bB\.?\s*PHARM\b",
                r"\bBACHELOR OF PHARMACY\b",
            ],
            "M.PHARM": [
                r"\bM\.?\s*PHARM\b",
                r"\bMASTER OF PHARMACY\b",
            ],
            "M.TECH": [
                r"\bM\.?\s*TECH\b",
                r"\bMASTER OF TECHNOLOGY\b",
            ],
            "M.SC": [
                r"\bM\.?\s*SC\b",
                r"\bMASTER OF SCIENCE\b",
            ],
            "B.SC": [
                r"\bB\.?\s*SC\b",
                r"\bBACHELOR OF SCIENCE\b",
            ],
        }

        for course, patterns in checks.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text_upper
                ):
                    courses.append(course)
                    break

        return courses

    # =========================================================
    # SINGLE COURSE DETECTION
    # =========================================================

    def detect_course(self, text: str):

        courses = self.detect_courses(text)

        if len(courses) == 1:
            return courses[0]

        return None

    # =========================================================
    # YEAR DETECTION
    # =========================================================

    def detect_year(self, text: str):

        match = re.search(
            r"(?:placement\s+year|batch|year|passing\s+out).*?"
            r"\b(20\d{2})\b",
            text,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

        years = re.findall(
            r"\b(20\d{2})\b",
            text
        )

        if years:
            return int(years[0])

        return None

    # =========================================================
    # PLACEMENT DETECTION
    # =========================================================

    def is_placement_document(
        self,
        document: Document
    ):

        metadata = document.metadata

        filename = str(
            metadata.get(
                "filename",
                ""
            )
        ).lower()

        topic = str(
            metadata.get(
                "topic",
                ""
            )
        ).lower()

        document_type = str(
            metadata.get(
                "document_type",
                ""
            )
        ).lower()

        return (
            "placement" in filename
            or topic == "placement"
            or document_type == "placement"
        )

    # =========================================================
    # ACADEMIC CALENDAR DETECTION
    # =========================================================

    def is_academic_calendar_document(
        self,
        document: Document
    ):

        metadata = document.metadata

        filename = str(
            metadata.get(
                "filename",
                ""
            )
        ).lower()

        topic = str(
            metadata.get(
                "topic",
                ""
            )
        ).lower()

        document_type = str(
            metadata.get(
                "document_type",
                ""
            )
        ).lower()

        category = str(
            metadata.get(
                "category",
                ""
            )
        ).lower()

        return (
            "academiccalendar" in filename
            or "academic calendar" in filename
            or topic == "academic calendar"
            or document_type == "academic_calendar"
            or "academiccalendar" in category
        )

    # =========================================================
    # ACADEMIC CALENDAR COURSE GROUP
    # =========================================================

    def detect_calendar_group(
        self,
        text: str
    ):

        text_upper = text.upper()

        # PG
        if re.search(
            r"\bALL\s+PG\s+STUDENTS\b"
            r"|\bPG\s+STUDENTS\b"
            r"|\bPOST\s*GRADUATE\b",
            text_upper
        ):
            return "PG"

        # UG
        if re.search(
            r"\bALL\s+UG\s+STUDENTS\b"
            r"|\bUG\s+STUDENTS\b"
            r"|\bUNDER\s*GRADUATE\b",
            text_upper
        ):
            return "UG"

        # PhD
        if re.search(
            r"\bALL\s+PH\.?\s*D\.?\s+STUDENTS\b"
            r"|\bPH\.?\s*D\.?\s+STUDENTS\b"
            r"|\bDOCTORAL\s+STUDENTS\b",
            text_upper
        ):
            return "PHD"

        return None

    # =========================================================
    # ACADEMIC CALENDAR SPLITTER
    # =========================================================

    def split_academic_calendar(
        self,
        document: Document
    ):

        text = document.page_content.strip()

        if not text:
            return []

        base_metadata = document.metadata.copy()

        base_metadata["document_type"] = (
            "academic_calendar"
        )

        base_metadata["topic"] = (
            "Academic Calendar"
        )

        # -----------------------------------------------------
        # Detect year
        # -----------------------------------------------------

        year = self.detect_year(text)

        if year:
            base_metadata["year"] = year

        # -----------------------------------------------------
        # Detect semester
        # -----------------------------------------------------

        text_upper = text.upper()

        if "SPRING" in text_upper:
            base_metadata["semester"] = "Spring"

        elif "MONSOON" in text_upper:
            base_metadata["semester"] = "Monsoon"

        # -----------------------------------------------------
        # Find UG / PG / PhD sections
        # -----------------------------------------------------

        pattern = re.compile(
            r"^(?:"
            r"Academic Calendar for All UG Students.*|"
            r"Academic Calendar for All PG Students.*|"
            r"Academic Calendar for All Ph\.?\s*D\.?\s*Students.*|"
            r"Academic Calendar.*UG.*|"
            r"Academic Calendar.*PG.*|"
            r"Academic Calendar.*Ph\.?\s*D.*"
            r")$",
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(
            pattern.finditer(text)
        )

        # -----------------------------------------------------
        # If headings were not detected, determine group
        # from complete page.
        # -----------------------------------------------------

        if not matches:

            group = self.detect_calendar_group(
                text
            )

            metadata = base_metadata.copy()

            metadata["course"] = group

            metadata["calendar_group"] = group

            metadata["section"] = (
                f"{group} Academic Calendar"
                if group
                else "Academic Calendar"
            )

            return [
                Document(
                    page_content=text,
                    metadata=metadata
                )
            ]

        sections = []

        for i, match in enumerate(matches):

            start = match.start()

            if i + 1 < len(matches):

                end = matches[
                    i + 1
                ].start()

            else:

                end = len(text)

            body = text[
                start:end
            ].strip()

            if not body:
                continue

            heading = match.group().strip()

            group = self.detect_calendar_group(
                heading
            )

            # If heading does not identify it,
            # check the section body.
            if not group:

                group = self.detect_calendar_group(
                    body
                )

            metadata = base_metadata.copy()

            metadata["course"] = group

            metadata["calendar_group"] = group

            metadata["section"] = heading

            sections.append(
                Document(
                    page_content=body,
                    metadata=metadata
                )
            )

        return sections

    # =========================================================
    # PLACEMENT SPLITTER
    # =========================================================

    def split_placement_document(
        self,
        document: Document
    ):

        text = document.page_content.strip()

        if not text:
            return []

        metadata = document.metadata.copy()

        courses = self.detect_courses(text)

        if courses:
            metadata["courses"] = courses

        if len(courses) == 1:
            metadata["course"] = courses[0]

        else:
            metadata["course"] = None

        year = self.detect_year(text)

        if year:
            metadata["year"] = year

        metadata["section"] = "Placement Data"

        metadata["document_type"] = "placement"

        return [
            Document(
                page_content=text,
                metadata=metadata
            )
        ]

    # =========================================================
    # NORMAL DOCUMENT SPLITTER
    # =========================================================

    def split_normal_document(
        self,
        document: Document
    ):

        text = document.page_content.strip()

        if not text:
            return []

        # ---------------------------------------------------------
        # Detect the course scope from the COMPLETE source document.
        #
        # This is important for multi-page PDFs such as Fees.pdf:
        # a later section may not repeat the course name, while the
        # source document clearly contains the course heading/table.
        # ---------------------------------------------------------

        document_courses = self.detect_courses(text)

        base_metadata = document.metadata.copy()

        if document_courses:

            base_metadata["courses"] = list(
                document_courses
            )

            if len(document_courses) == 1:

                base_metadata["course"] = (
                    document_courses[0]
                )

            else:

                # Multiple courses are covered by the source.
                # Do NOT keep a stale loader value such as MCA.
                base_metadata["course"] = None

        # ---------------------------------------------------------
        # Detect year once from the complete source.
        # ---------------------------------------------------------

        document_year = self.detect_year(text)

        if document_year:
            base_metadata["year"] = document_year

        # ---------------------------------------------------------
        # Section headings
        # ---------------------------------------------------------

        pattern = re.compile(
            r"^(?:"
            r"Master of Computer Application|"
            r"Master of Business Administration|"
            r"Bachelor of Computer Application|"
            r"Bachelor of Business Administration|"
            r"Bachelor of Technology|"
            r"Bachelor of Architecture|"
            r"Bachelor of Pharmacy|"
            r"Master of Pharmacy|"
            r"Master of Technology(?:\s*&\s*Master of Planning)?|"
            r"Master of Science|"
            r"Bachelor of Science|"
            r"B\.?\s*Tech|"
            r"B\.?\s*Arch|"
            r"B\.?\s*Pharm|"
            r"M\.?\s*Pharm|"
            r"M\.?\s*Tech|"
            r"M\.?\s*Sc|"
            r"B\.?\s*Sc|"
            r"MCA|"
            r"MBA|"
            r"BCA|"
            r"BBA|"
            r"BTech"
            r")[^\n]{0,120}$",
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(
            pattern.finditer(text)
        )

        # ---------------------------------------------------------
        # No course heading detected:
        # preserve the document-level metadata.
        # ---------------------------------------------------------

        if not matches:

            return [
                Document(
                    page_content=text,
                    metadata=base_metadata
                )
            ]

        sections = []

        for i, match in enumerate(matches):

            start = match.start()

            if i + 1 < len(matches):

                end = matches[
                    i + 1
                ].start()

            else:

                end = len(text)

            body = text[
                start:end
            ].strip()

            if not body:
                continue

            heading = match.group().strip()

            metadata = base_metadata.copy()

            # -----------------------------------------------------
            # First preference: explicit course(s) in this section.
            # -----------------------------------------------------

            section_courses = self.detect_courses(
                body
            )

            if len(section_courses) == 1:

                metadata["course"] = (
                    section_courses[0]
                )

                metadata["courses"] = list(
                    section_courses
                )

            elif len(section_courses) > 1:

                metadata["course"] = None

                metadata["courses"] = list(
                    section_courses
                )

            # -----------------------------------------------------
            # If the section itself does not mention a course,
            # KEEP the complete source-document course scope.
            #
            # This prevents:
            #
            #     Fees section -> course=MCA
            #
            # merely because the loader had MCA as category.
            # -----------------------------------------------------

            metadata["section"] = heading

            sections.append(
                Document(
                    page_content=body,
                    metadata=metadata
                )
            )

        return sections

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def split_document(
        self,
        document: Document
    ):

        # Academic Calendar
        if self.is_academic_calendar_document(
            document
        ):

            return self.split_academic_calendar(
                document
            )

        # Placement
        if self.is_placement_document(
            document
        ):

            return self.split_placement_document(
                document
            )

        # Normal documents
        return self.split_normal_document(
            document
        )