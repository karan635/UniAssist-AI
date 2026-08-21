from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_index_manager
from app.services.rag.index_manager import IndexManager


router = APIRouter()


def _format_index_result(result):

    # -----------------------------------------
    # If rebuild()/sync() returns a dictionary
    # -----------------------------------------

    if isinstance(result, dict):

        return {
            "status": "FAISS Index Updated Successfully",
            **result
        }

    # -----------------------------------------
    # Fallback if it returns chunks
    # -----------------------------------------

    if isinstance(result, list):

        return {
            "status": "FAISS Index Updated Successfully",
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
        "status": "FAISS Index Updated Successfully",
        "result": str(result)
    }


@router.post("/index/rebuild")
def rebuild_index(
    manager: IndexManager = Depends(get_index_manager),
):
    """
    Full rebuild: reprocesses and re-embeds every PDF from scratch,
    regardless of whether anything changed. Slower, but useful if you
    ever suspect the index/manifest has drifted out of sync with the
    documents on disk and want a clean, known-good rebuild.
    """

    try:

        result = manager.rebuild()

        return _format_index_result(result)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Index rebuild failed: {str(e)}"
        )


@router.post("/index/sync")
def sync_index(
    manager: IndexManager = Depends(get_index_manager),
):
    """
    Incremental sync: only new, changed, or deleted PDFs are
    (re)processed -- unchanged files are skipped entirely. This is what
    you should call day-to-day after adding/updating/removing a
    document, instead of /index/rebuild.

    Falls back to a full rebuild automatically the very first time
    it's called (no existing index yet to patch).
    """

    try:

        result = manager.sync()

        return _format_index_result(result)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Index sync failed: {str(e)}"
        )