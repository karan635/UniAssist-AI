from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_pdf_loader_service
from app.services.knowledge.pdf_loader import PDFLoaderService

router = APIRouter()


@router.get("/load")
def load_pdf(
    loader: PDFLoaderService = Depends(get_pdf_loader_service),
):

    try:

        docs = loader.load_documents()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load PDFs: {str(e)}"
        )

    if not docs:

        raise HTTPException(
            status_code=404,
            detail="No PDF documents were found to load."
        )

    return {
        "documents": len(docs),
        "sample_metadata": docs[0].metadata
    }