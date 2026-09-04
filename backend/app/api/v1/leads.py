from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.services.crm.lead_service import LeadService

router = APIRouter()


class LeadCaptureRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    course_interest: str | None = None
    message: str | None = None
    source: str = "form"          # "form" | "auto"
    session_id: str | None = None


@router.post("/leads")
def create_lead(payload: LeadCaptureRequest):
    try:
        service = LeadService()
        result = service.capture_lead(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            course_interest=payload.course_interest,
            message=payload.message,
            source=payload.source,
            session_id=payload.session_id,
        )
        return {"success": True, **result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {e}")