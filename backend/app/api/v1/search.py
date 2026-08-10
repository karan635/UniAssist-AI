from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_index_manager
from app.services.rag.index_manager import IndexManager

router = APIRouter()


@router.get("/search")
def search(
    query: str,
    manager: IndexManager = Depends(get_index_manager),
):

    try:

        result = manager.search(query)

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

    return {
        "query": query,
        "analysis": result["analysis"],
        "documents": result["documents"],
        "context": result["context"]
    }