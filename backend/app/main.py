from dotenv import load_dotenv

from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.document import router as document_router
from app.api.v1.pdf_loader import router as pdf_loader_router
from app.api.v1.registry import router as registry_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.index import router as index_router
from app.api.v1.search import router as search_router
from app.api.v1.query import router as query_router
from app.api.v1.leads import router as leads_router
from app.api.v1 import chat

load_dotenv()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(
    chat.router,
    prefix="/api/v1",
    tags=["Chat"]
)

app.include_router(
    pdf_loader_router,
    prefix="/api/v1/pdf",
    tags=["PDF Loader"]
)

app.include_router(
    search_router,
    prefix="/api/v1",
    tags=["Search"]
)

app.include_router(
    query_router,
    prefix="/api/v1",
    tags=["Query Analysis"]
)


app.include_router(
    index_router,
    prefix="/api/v1",
    tags=["Index Manager"]
)

app.include_router(
    registry_router,
    prefix="/api/v1",
    tags=["Knowledge Registry"]
)

app.include_router(
    knowledge_router,
    prefix="/api/v1",
    tags=["Knowledge Manager"]
)

app.include_router(
    document_router,
    prefix="/api/v1",
    tags=["Documents"]
)

app.include_router(
    leads_router,
    prefix="/api/v1",
    tags=["Leads"]
)