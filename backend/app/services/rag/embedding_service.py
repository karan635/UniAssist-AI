"""Embedding generation service."""

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingService:
    """
    Generates embeddings using HuggingFace.
    """

    def __init__(self):

        self.embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={
                "device": "cpu"
            },
            encode_kwargs={
                "normalize_embeddings": True
            }
        )

    def get_embeddings(self):

        return self.embedding_model 