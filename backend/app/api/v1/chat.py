from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_chat_service
from app.core.exceptions import UniAssistException
from app.services.ai.chat_service import ChatService

router = APIRouter()


@router.post("/chat")
def chat(
    request: dict,
    service: ChatService = Depends(get_chat_service),
):

    question = request.get("question")
    session_id = request.get("session_id")

    if not question:

        return {
            "error": "Question is required."
        }

    try:

        return service.chat(question, session_id=session_id)

    except UniAssistException as e:

        raise HTTPException(status_code=502, detail=e.message)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Chat request failed: {str(e)}"
        )