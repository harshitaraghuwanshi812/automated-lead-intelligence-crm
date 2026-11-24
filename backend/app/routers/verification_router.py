from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import VerificationTriggerRequest, VerificationResultOut
from app.services import verification_service
from app.auth.security import get_current_user
from app.database import fetch_all

router = APIRouter(prefix="/verification", tags=["Email Verification"])

@router.post("/verify", response_model=VerificationResultOut)
async def verify_email(payload: VerificationTriggerRequest, current_user: dict = Depends(get_current_user)):
    email = payload.email
    if not email and payload.contact_method_id:
        cm = fetch_all("SELECT value FROM contact_methods WHERE id = %s", [payload.contact_method_id])
        if cm:
            email = cm[0]["value"]

    if not email:
        raise HTTPException(status_code=400, detail="Email address or valid contact_method_id is required.")

    result = verification_service.verify_email_address(
        email=email,
        contact_method_id=payload.contact_method_id
    )
    return VerificationResultOut(**result)

@router.get("/results", response_model=List[VerificationResultOut])
async def list_verification_results():
    rows = fetch_all("SELECT * FROM verification_results ORDER BY checked_at DESC LIMIT 50")
    return [VerificationResultOut(**r) for r in rows]
