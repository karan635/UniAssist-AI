import re


class QueryAnalyzer:

    def __init__(self):

        self.courses = [
            "MCA",
            "BCA",
            "BBA",
            "B.TECH",
            "MBA",
            "MTECH"
        ]

        self.topics = {

            "Admission": [
                "admission",
                "admissions"
            ],

            "Fees": [
                "fee",
                "fees",
                "tuition",
                "cost"
            ],

            "Placement": [
                "placement",
                "placements",
                "package",
                "company",
                "companies",
                "recruiter",
                "salary"
            ],

            "Eligibility": [
                "eligibility",
                "eligible",
                "criteria"
            ],

            "Scholarship": [
                "scholarship"
            ]
        }

    def analyze(self, query: str):

        result = {

            "course": None,

            "topic": None,

            "intent": "information",

            "year": None,

            "language": "English"

        }

        upper_query = query.upper()

        # Detect Course

        for course in self.courses:

            if course.upper() in upper_query:

                result["course"] = course

                break

        # Detect Topic

        lower_query = query.lower()

        for topic, keywords in self.topics.items():

            if any(keyword in lower_query for keyword in keywords):

                result["topic"] = topic

                break

        # Detect Year

        year = re.search(r"20\d{2}", query)

        if year:

            result["year"] = int(year.group())

        # Detect Download

        if "download" in lower_query:

            result["intent"] = "download"

        return result