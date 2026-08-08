import re


class QueryAnalyzer:

    def __init__(self):

        self.courses = [
            "MCA",
            "BCA",
            "BBA",
            "B.TECH",
            "MBA",
            "MTECH",
            "M.TECH",
            "B.ARCH",
            "B.PHARM",
            "M.PHARM",
            "B.SC",
            "M.SC",
        ]

        self.topics = {

            "Admission": [
                "admission",
                "admissions",
                "apply",
                "application",
                "entrance",
            ],

            "Fees": [
                "fee",
                "fees",
                "tuition",
                "cost",
                "expense",
                "expenditure",
            ],

            "Placement": [
                "placement",
                "placements",
                "package",
                "company",
                "companies",
                "recruiter",
                "recruiters",
                "salary",
                "offer",
                "offers",
                "highest package",
                "minimum package",
            ],

            "Eligibility": [
                "eligibility",
                "eligible",
                "criteria",
                "qualification",
                "qualifications",
            ],

            "Scholarship": [
                "scholarship",
                "scholarships",
                "financial aid",
            ],

            # =============================================
            # ACADEMIC CALENDAR
            # =============================================

            "Academic Calendar": [

                "academic calendar",
                "calendar",

                "semester start",
                "semester starts",
                "semester begin",
                "semester begins",

                "semester end",
                "semester ends",

                "spring",
                "spring semester",

                "monsoon",
                "monsoon semester",

                "quiz",
                "quiz 1",
                "quiz 2",

                "mid semester",
                "mid-semester",
                "mid semester examination",
                "mid-semester examination",

                "end semester",
                "end-semester",
                "end semester examination",
                "end-semester examination",

                "examination",
                "exam",

                "registration",
                "registration date",

                "orientation",

                "classes start",
                "classes begin",
                "class commencement",
            ]
        }

    # =====================================================
    # COURSE NORMALIZATION
    # =====================================================

    def normalize_course(self, course):

        if not course:
            return None

        course = course.upper().strip()

        mapping = {

            "BTECH": "B.TECH",
            "B.TECH": "B.TECH",
            "B.TECH.": "B.TECH",

            "MTECH": "M.TECH",
            "M.TECH": "M.TECH",
            "M.TECH.": "M.TECH",

            "MSC": "M.SC",
            "M.SC": "M.SC",
            "M.SC.": "M.SC",

            "BSC": "B.SC",
            "B.SC": "B.SC",
            "B.SC.": "B.SC",

            "BPHARM": "B.PHARM",
            "B.PHARM": "B.PHARM",
            "B.PHARM.": "B.PHARM",

            "MPHARM": "M.PHARM",
            "M.PHARM": "M.PHARM",
            "M.PHARM.": "M.PHARM",

        }

        return mapping.get(
            course,
            course
        )

    # =====================================================
    # ANALYZE
    # =====================================================

    def analyze(self, query: str):

        result = {

            "course": None,

            "topic": None,

            "intent": "information",

            "year": None,

            "language": "English"

        }

        upper_query = query.upper()

        lower_query = query.lower()

        # =================================================
        # COURSE
        # =================================================

        # Important:
        # Check longer/specific course names first.

        course_patterns = {

            "B.TECH": [
                r"\bB[\s.]?TECH\b",
                r"\bBTECH\b",
                r"\bB\. TECH\b",
            ],

            "MCA": [
                r"\bMCA\b",
                r"\bMASTER OF COMPUTER APPLICATIONS?\b",
            ],

            "BCA": [
                r"\bBCA\b",
                r"\bBACHELOR OF COMPUTER APPLICATIONS?\b",
            ],

            "BBA": [
                r"\bBBA\b",
                r"\bBACHELOR OF BUSINESS ADMINISTRATION\b",
            ],

            "MBA": [
                r"\bMBA\b",
                r"\bMASTER OF BUSINESS ADMINISTRATION\b",
            ],

            "M.TECH": [
                r"\bM[\s.]?TECH\b",
                r"\bMTECH\b",
            ],

            "B.ARCH": [
                r"\bB[\s.]?ARCH\b",
            ],

            "B.PHARM": [
                r"\bB[\s.]?PHARM\b",
            ],

            "M.PHARM": [
                r"\bM[\s.]?PHARM\b",
            ],

            "B.SC": [
                r"\bB[\s.]?SC\b",
            ],

            "M.SC": [
                r"\bM[\s.]?SC\b",
            ],
        }

        for course, patterns in course_patterns.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    upper_query
                ):

                    result["course"] = course

                    break

            if result["course"]:
                break

        # =================================================
        # TOPIC
        # =================================================

        for topic, keywords in self.topics.items():

            for keyword in keywords:

                # Exact phrase/keyword matching
                if keyword in lower_query:

                    result["topic"] = topic

                    break

            if result["topic"]:
                break

        # =================================================
        # YEAR
        # =================================================

        year = re.search(
            r"\b(20\d{2})\b",
            query
        )

        if year:

            result["year"] = int(
                year.group(1)
            )

        # =================================================
        # INTENT
        # =================================================

        if "download" in lower_query:

            result["intent"] = "download"

        elif any(
            word in lower_query
            for word in [
                "when",
                "what date",
                "which date",
                "date of",
                "schedule"
            ]
        ):

            result["intent"] = "information"

        return result