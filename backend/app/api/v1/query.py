from fastapi import APIRouter

from app.services.ai.query_analyzer import QueryAnalyzer

router = APIRouter()

@router.get("/analyze")
def analyze(query: str):

    analyzer = QueryAnalyzer()

    return analyzer.analyze(query)