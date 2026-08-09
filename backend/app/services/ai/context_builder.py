"""Build clean and structured context for the LLM."""

import re

from langchain_core.documents import Document


class ContextBuilder:

    def build_context(
        self,
        documents: list[Document]
    ) -> str:

        if not documents:
            return "No relevant documents were found."

        context_parts = []

        for index, document in enumerate(
            documents,
            start=1
        ):

            metadata = document.metadata

            filename = metadata.get(
                "filename",
                metadata.get("source", "Unknown")
            )

            page = metadata.get(
                "page_label",
                metadata.get("page", "Unknown")
            )

            course = (
                metadata.get("course")
                or metadata.get("category")
            )

            courses = metadata.get(
                "courses",
                []
            )

            # -------------------------------------------------
            # COURSE DISPLAY
            # -------------------------------------------------

            if courses:

                if isinstance(courses, list):

                    course_display = ", ".join(
                        str(course)
                        for course in courses
                    )

                else:

                    course_display = str(courses)

            elif course:

                course_display = str(course)

            else:

                course_display = "Not specified"

            topic = metadata.get(
                "topic",
                "Not specified"
            )

            year = metadata.get(
                "year",
                "Not specified"
            )

            semester = metadata.get(
                "semester",
                "Not specified"
            )

            section = metadata.get(
                "section",
                "Not specified"
            )

            document_type = metadata.get(
                "document_type",
                "Not specified"
            )

            content = document.page_content

            # -------------------------------------------------
            # NORMAL CONTEXT
            # -------------------------------------------------

            block = f"""
========== DOCUMENT {index} ==========

Filename:
{filename}

Page:
{page}

Course(s):
{course_display}

Topic:
{topic}

Year:
{year}

Semester:
{semester}

Document Type:
{document_type}

Section:
{section}

Content:
{content}
"""

            # -------------------------------------------------
            # PLACEMENT TABLE STRUCTURE
            # -------------------------------------------------

            if (
                str(document_type).lower() == "placement"
                or str(topic).lower() == "placement"
                or "placement" in filename.lower()
            ):

                placement_summary = (
                    self._build_placement_summary(
                        content
                    )
                )

                if placement_summary:

                    block += f"""

========== STRUCTURED PLACEMENT DATA ==========

{placement_summary}
"""

            context_parts.append(
                block.strip()
            )

        return "\n\n".join(
            context_parts
        )

    # =========================================================
    # PLACEMENT TABLE PARSER
    # =========================================================

    def _build_placement_summary(
        self,
        content: str
    ) -> str:

        """
        Recover the table structure that is lost when
        the PDF table is converted into plain text.

        Expected placement table:

        B.Tech:
            Electronics & Communication
            Computer Science
            Electrical & Electronics

        MCA

        Total Offers
            B.Tech ECE
            B.Tech CSE
            B.Tech EEE
            MCA

        Eligible Students
            B.Tech ECE
            B.Tech CSE
            B.Tech EEE
            MCA
        """

        # -----------------------------------------------------
        # Find the numeric rows immediately before the
        # placement summary section.
        #
        # Example:
        #
        # 17 33 6 7
        # 45 48 13 23
        # MAXIMUM PACKAGE OFFERED
        # -----------------------------------------------------

        marker = re.search(
            r"MAXIMUM\s+PACKAGE\s+OFFERED",
            content,
            re.IGNORECASE
        )

        if not marker:
            return ""

        before_package = content[:marker.start()]

        # -----------------------------------------------------
        # Remove package values that may appear before the
        # "MAXIMUM PACKAGE OFFERED" label in PDF-extracted text.
        #
        # Examples:
        #   24.50 LPA
        #   400000
        #
        # or:
        #   22.60 LPA
        #   4.00 LPA
        #
        # These numbers are NOT placement-table values.
        # -----------------------------------------------------

        package_cleaned = re.sub(
            r"\d+(?:\.\d+)?\s*LPA",
            "",
            before_package,
            flags=re.IGNORECASE
        )

        # Remove a trailing standalone minimum-package value,
        # e.g. 400000, when it remains after removing the LPA value.
        package_cleaned = re.sub(
            r"\b\d+\b\s*$",
            "",
            package_cleaned.strip()
        )

        # -----------------------------------------------------
        # Extract numeric values from the placement table.
        #
        # The final 8 values are:
        #   4 Total Offers
        #   4 Eligible Students
        #
        # Decimal package values are protected from being
        # split into separate integers.
        # -----------------------------------------------------

        numbers = re.findall(
            r"(?<![\d.])\d+(?![\d.])",
            package_cleaned
        )

        if len(numbers) < 8:
            return ""

        values = [
            int(value)
            for value in numbers[-8:]
        ]

        total_offers = values[:4]

        eligible_students = values[4:]

        # -----------------------------------------------------
        # Table columns confirmed from Placement_2024.pdf
        # -----------------------------------------------------

        btech_ece = total_offers[0]
        btech_cse = total_offers[1]
        btech_eee = total_offers[2]
        mca_offers = total_offers[3]

        btech_ece_eligible = eligible_students[0]
        btech_cse_eligible = eligible_students[1]
        btech_eee_eligible = eligible_students[2]
        mca_eligible = eligible_students[3]

        btech_total_offers = (
            btech_ece
            + btech_cse
            + btech_eee
        )

        btech_total_eligible = (
            btech_ece_eligible
            + btech_cse_eligible
            + btech_eee_eligible
        )

        return f"""
The placement table contains separate B.Tech and MCA columns.

B.TECH
- Electronics & Communication:
  Total Offers: {btech_ece}
  Eligible Students: {btech_ece_eligible}

- Computer Science:
  Total Offers: {btech_cse}
  Eligible Students: {btech_cse_eligible}

- Electrical & Electronics:
  Total Offers: {btech_eee}
  Eligible Students: {btech_eee_eligible}

- B.Tech Total Offers:
  {btech_total_offers}

- B.Tech Total Eligible Students:
  {btech_total_eligible}

MCA
- Total Offers:
  {mca_offers}

- Eligible Students:
  {mca_eligible}
""".strip()
