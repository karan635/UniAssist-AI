from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_knowledge_manager
from app.services.knowledge.knowledge_manager import KnowledgeManager

router = APIRouter()


@router.get("/knowledge")
def knowledge(
    manager: KnowledgeManager = Depends(get_knowledge_manager),
):

    try:

        docs = manager.load_documents()

        registry = manager.build_registry()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load knowledge base: {str(e)}"
        )

    return {
        "documents": len(docs),
        "courses": list(registry.keys()),
        "registry": registry
    }