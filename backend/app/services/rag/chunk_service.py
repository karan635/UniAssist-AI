from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class ChunkService:
    """
    Splits documents into chunks while preserving metadata.
    """

    def __init__(
        self,
        chunk_size: int = 2500,
        chunk_overlap: int = 300,
    ):

        self.normal_splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

        self.placement_splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=2500,
                chunk_overlap=300,
            )
        )

    def split_documents(
        self,
        documents: List[Document],
    ) -> List[Document]:

        chunks = []

        for document in documents:

            if (
                document.metadata.get(
                    "topic"
                ) == "Placement"
                or document.metadata.get(
                    "document_type"
                ) == "placement"
            ):

                splitter = self.placement_splitter

            else:

                splitter = self.normal_splitter

            document_chunks = (
                splitter.split_documents(
                    [document]
                )
            )

            chunks.extend(document_chunks)

        # -----------------------------------------------------
        # Add chunk metadata
        # -----------------------------------------------------

        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            course = chunk.metadata.get(
                "course",
                "UNKNOWN"
            )

            topic = chunk.metadata.get(
                "topic",
                "UNKNOWN"
            )

            year = chunk.metadata.get(
                "year",
                ""
            )

            chunk.metadata["chunk_id"] = (
                f"{course}_"
                f"{topic}_"
                f"{year}_"
                f"{index}"
            )

            chunk.metadata[
                "chunk_number"
            ] = index

        return chunks