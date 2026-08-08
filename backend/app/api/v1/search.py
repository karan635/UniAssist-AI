from fastapi import APIRouter

from app.services.rag.index_manager import IndexManager

router = APIRouter()


@router.get("/search")
def search(query: str):

    manager = IndexManager()

    result = manager.search(query)

    return {
        "query": query,
        "analysis": result["analysis"],
        "documents": result["documents"],
        "context": result["context"]
    }