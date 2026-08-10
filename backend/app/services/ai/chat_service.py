from typing import Optional

from app.services.rag.index_manager import IndexManager
from app.services.ai.groq_client import GroqClient
from app.services.ai.response_builder import ResponseBuilder
from app.services.prompts.prompt_router import PromptRouter


class ChatService:

    def __init__(self, index_manager: Optional[IndexManager] = None):

        self.index_manager = index_manager or IndexManager()

        self.groq_client = GroqClient()

        self.response_builder = ResponseBuilder()

        self.prompt_router = PromptRouter()

    def chat(self, question: str):

        retrieval = self.index_manager.search(question)

        prompt = self.prompt_router.build(
            question=question,
            context=retrieval["context"],
            analysis=retrieval["analysis"]
        )

        answer = self.groq_client.generate(prompt)

        return self.response_builder.build(
            answer=answer,
            analysis=retrieval["analysis"],
            documents=retrieval["documents"]
        )