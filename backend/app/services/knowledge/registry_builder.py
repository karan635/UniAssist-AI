from pathlib import Path


class RegistryBuilder:
    """
    Builds a registry of all available documents.
    """

    def __init__(self, documents_path: str = "data/documents"):
        self.documents_path = Path(documents_path)

    def build(self) -> dict:

        registry = {}

        for course_folder in self.documents_path.iterdir():

            if not course_folder.is_dir():
                continue

            course = course_folder.name

            registry[course] = {}

            for pdf in course_folder.glob("*.pdf"):

                filename = pdf.stem

                registry[course][filename] = {
                    "path": str(pdf)
                }

        return registry