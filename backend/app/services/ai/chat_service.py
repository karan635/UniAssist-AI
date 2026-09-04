from typing import Optional

from app.services.rag.index_manager import IndexManager
from app.services.ai.groq_client import GroqClient
from app.services.ai.response_builder import ResponseBuilder
from app.services.prompts.prompt_router import PromptRouter
from app.services.crm.lead_intent_tracker import lead_intent_tracker


class ChatService:

    def __init__(self, index_manager: Optional[IndexManager] = None):

        self.index_manager = index_manager or IndexManager()

        self.groq_client = GroqClient()

        self.response_builder = ResponseBuilder()

        self.prompt_router = PromptRouter()

    def chat(self, question: str, session_id: Optional[str] = None):

        retrieval = self.index_manager.search(question)

        prompt = self.prompt_router.build(
            question=question,
            context=retrieval["context"],
            analysis=retrieval["analysis"]
        )

        answer = self.groq_client.generate(prompt)

        response = self.response_builder.build(
            answer=answer,
            analysis=retrieval["analysis"],
            documents=retrieval["documents"]
        )

        # Auto-detected lead prompt: fires once per session, the turn the
        # interest score crosses LEAD_INTEREST_THRESHOLD (see
        # LeadIntentTracker). session_id is optional so any caller that
        # doesn't send one just never gets the prompt -- nothing breaks.
        if session_id:
            topic = retrieval["analysis"].get("topic")
            response["lead_prompt"] = lead_intent_tracker.record_query(
                session_id, topic
            )
        else:
            response["lead_prompt"] = False

        return response