from fastapi import APIRouter, HTTPException

from app.services.rag.document_loader import DocumentLoader
from app.services.rag.text_splitter import TextSplitterService

router = APIRouter()


@router.get("/chunks")
def chunks():

    try:

        loader = DocumentLoader()

        docs = loader.load_documents()

        splitter = TextSplitterService()

        chunks = splitter.split_documents(docs)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to build chunks: {str(e)}"
        )

    if not chunks:

        raise HTTPException(
            status_code=404,
            detail="No documents/chunks were found."
        )

    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "sample_chunk": chunks[0].page_content[:500],
        "metadata": chunks[0].metadata
    }