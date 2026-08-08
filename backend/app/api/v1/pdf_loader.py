from fastapi import APIRouter


from app.services.knowledge.pdf_loader import PDFLoaderService

router = APIRouter()

@router.get("/load")

def load_pdf():

    loader = PDFLoaderService()

    docs = loader.load_documents()

    return {
        "documents": len(docs),
        "sample_metadata": docs[0].metadata
    }