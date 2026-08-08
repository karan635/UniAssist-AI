from fastapi import APIRouter

from app.services.knowledge.knowledge_manager import KnowledgeManager

router = APIRouter()


@router.get("/knowledge")
def knowledge():

    manager = KnowledgeManager()

    docs = manager.load_documents()

    registry = manager.build_registry()

    return {
        "documents": len(docs),
        "courses": list(registry.keys()),
        "registry": registry
    }