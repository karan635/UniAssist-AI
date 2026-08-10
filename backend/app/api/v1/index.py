from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_index_manager
from app.services.rag.index_manager import IndexManager


router = APIRouter()


@router.post("/index/rebuild")
def rebuild_index(
    manager: IndexManager = Depends(get_index_manager),
):

    try:

        # -----------------------------------------
        # Run complete indexing pipeline
        # -----------------------------------------

        result = manager.rebuild()

        # -----------------------------------------
        # If rebuild() returns a dictionary
        # -----------------------------------------

        if isinstance(result, dict):

            return {
                "status": "FAISS Index Created Successfully",
                **result
            }

        # -----------------------------------------
        # Fallback if rebuild() returns chunks
        # -----------------------------------------

        if isinstance(result, list):

            return {
                "status": "FAISS Index Created Successfully",
                "total_chunks": len(result),
                "sample_chunk": (
                    {
                        "text": result[0].page_content[:500],
                        "metadata": result[0].metadata
                    }
                    if result
                    else None
                )
            }

        # -----------------------------------------
        # Unknown return type
        # -----------------------------------------

        return {
            "status": "FAISS Index Created Successfully",
            "result": str(result)
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Index rebuild failed: {str(e)}"
        )