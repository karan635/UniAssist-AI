from fastapi import APIRouter

from app.services.ai.chat_service import ChatService

router = APIRouter()


@router.post("/chat")
def chat(request: dict):

    question = request.get("question")

    if not question:

        return {
            "error": "Question is required."
        }

    service = ChatService()

    return service.chat(question)