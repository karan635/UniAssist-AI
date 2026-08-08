from fastapi import APIRouter

from app.services.rag.document_loader import DocumentLoader
from app.services.rag.text_splitter import TextSplitterService

router = APIRouter()


@router.get("/chunks")
def chunks():

    loader = DocumentLoader()

    docs = loader.load_documents()

    splitter = TextSplitterService()

    chunks = splitter.split_documents(docs)

    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "sample_chunk": chunks[0].page_content[:500],
        "metadata": chunks[0].metadata
    }