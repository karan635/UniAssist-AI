import re

from langchain_core.documents import Document


class SectionSplitter:

    COURSE_PATTERNS = {
        "B.TECH": [
            r"\bB\.?\s*Tech\b",
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

        # Prefer explicit placement/batch/year expressions

        match = re.search(
            r"(?:placement\s+year|batch|year|passing\s+out).*?"
            r"\b(20\d{2})\b",
            text,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

        # General fallback

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

    def is_placement_document(self, document: Document):

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

        # Detect all courses represented
        courses = self.detect_courses(text)

        if courses:
            metadata["courses"] = courses

        # IMPORTANT:
        # Do NOT assign one course to a multi-course
        # placement document.
        #
        # Example:
        #
        # Placement_2026.pdf
        #     B.Tech
        #     MCA
        #
        # Therefore:
        #
        # course = None
        # courses = ["B.TECH", "MCA"]

        if len(courses) == 1:
            metadata["course"] = courses[0]
        else:
            metadata["course"] = None

        # Year
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

        text = document.page_content

        pattern = re.compile(
            r"^(?:"
            r"Master of Computer Application|"
            r"Master of Business Administration|"
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
            r"BBA"
            r")[^\n]{0,120}$",
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(
            pattern.finditer(text)
        )

        if not matches:

            # Do not silently lose documents
            metadata = document.metadata.copy()

            course = self.detect_course(text)

            if course:
                metadata["course"] = course

            year = self.detect_year(text)

            if year:
                metadata["year"] = year

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
                end = matches[i + 1].start()
            else:
                end = len(text)

            body = text[start:end].strip()

            if not body:
                continue

            heading = match.group().strip()

            metadata = document.metadata.copy()

            course = self.detect_course(
                body
            )

            if course:
                metadata["course"] = course

            year = self.detect_year(
                body
            )

            if year:
                metadata["year"] = year

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

        # -----------------------------------------
        # PLACEMENT
        # -----------------------------------------

        if self.is_placement_document(
            document
        ):

            return self.split_placement_document(
                document
            )

        # -----------------------------------------
        # NORMAL DOCUMENT
        # -----------------------------------------

        return self.split_normal_document(
            document
        )