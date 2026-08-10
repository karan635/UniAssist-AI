from fastapi import APIRouter, HTTPException

from app.services.ai.query_analyzer import QueryAnalyzer

router = APIRouter()

# QueryAnalyzer does no model loading / I/O, so unlike IndexManager /
# ChatService there's no per-request reload cost to fix here -- it's cheap
# to construct. Kept as-is aside from basic input validation.
_analyzer = QueryAnalyzer()


@router.get("/analyze")
def analyze(query: str):

    if not query or not query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query parameter cannot be empty."
        )

    return _analyzer.analyze(query)