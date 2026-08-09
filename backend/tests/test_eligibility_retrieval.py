import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("DEBUG", "true")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document

from app.services.ai.metadata_filter import MetadataFilter
from app.services.ai.context_builder import ContextBuilder
from app.services.rag.section_splitter import SectionSplitter


class EligibilityRetrievalTests(unittest.TestCase):
    def test_eligibility_section_in_admission_brochure_matches(self):
        document = Document(
            page_content="Eligibility Criteria: candidates must hold a Bachelor's Degree.",
            metadata={"topic": "Admission", "course": "MCA"},
        )

        self.assertTrue(
            MetadataFilter().topic_matches(document, "Eligibility")
        )

    def test_non_eligibility_admission_section_is_not_returned(self):
        document = Document(
            page_content="Application forms must be submitted before the deadline.",
            metadata={"topic": "Admission", "course": "MCA"},
        )

        self.assertFalse(
            MetadataFilter().topic_matches(document, "Eligibility")
        )

    def test_existing_category_metadata_matches_the_requested_course(self):
        document = Document(
            page_content="Eligibility Criteria for applicants.",
            metadata={"topic": "Admission", "category": "MCA"},
        )

        self.assertTrue(
            MetadataFilter().course_matches(document, "MCA")
        )

    def test_context_displays_legacy_category_as_the_course(self):
        document = Document(
            page_content="Eligibility Criteria for applicants.",
            metadata={"topic": "Admission", "category": "MCA", "page": 3},
        )

        self.assertIn(
            "Course(s):\nMCA",
            ContextBuilder().build_context([document]),
        )

    def test_section_splitter_preserves_folder_course_metadata(self):
        document = Document(
            page_content="BCA\nEligibility Criteria\nCandidates must qualify.",
            metadata={"topic": "Admission", "course": "BCA"},
        )

        sections = SectionSplitter().split_normal_document(document)

        self.assertTrue(sections)
        self.assertEqual(sections[0].metadata["course"], "BCA")

    def test_eligibility_continuation_keeps_its_brochure_course(self):
        document = Document(
            page_content="B.Sc. in Computer Science is an accepted qualification.",
            metadata={"topic": "Admission", "course": "MCA"},
        )

        sections = SectionSplitter().split_normal_document(document)

        self.assertEqual(sections[0].metadata["course"], "MCA")


if __name__ == "__main__":
    unittest.main()
