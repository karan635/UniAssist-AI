from pathlib import Path


class MetadataBuilder:
    """
    Builds metadata for every document.

    This class is responsible only for creating
    metadata from the file path.
    """

    def build(self, pdf_path: Path) -> dict:

        course = pdf_path.parent.name

        filename = pdf_path.stem

        metadata = {
            "course": course,
            "filename": pdf_path.name,
            "topic": filename
        }

        # Detect Placement Year
        if "Placement_" in filename:

            metadata["topic"] = "Placement"

            parts = filename.split("_")

            if len(parts) > 1 and parts[-1].isdigit():
                metadata["year"] = int(parts[-1])

        # Detect Fees

        elif filename == "Fees":

            metadata["topic"] = "Fees"

        # Detect Admission

        elif filename == "Admission":

            metadata["topic"] = "Admission"

        return metadata