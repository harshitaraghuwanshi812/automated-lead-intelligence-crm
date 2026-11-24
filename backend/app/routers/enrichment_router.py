from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import EnrichmentTriggerRequest, EnrichmentRequestOut
from app.services import enrichment_service
from app.auth.security import get_current_user, require_roles
from app.database import fetch_all

router = APIRouter(prefix="/enrichment", tags=["Contact Enrichment"])

@router.get("/queue")
async def get_enrichment_queue():
    """Returns opportunities and contacts with missing recruiter email or needing research."""
    return enrichment_service.get_enrichment_queue()

@router.post("/enrich", response_model=EnrichmentRequestOut)
async def trigger_manual_enrichment(
    payload: EnrichmentTriggerRequest,
    current_user: dict = Depends(require_roles(["researcher", "admin"]))
):
    """
    Manually enriches contact with ContactOut / Snov.io.
    Requires explicit credit confirmation.
    """
    result = enrichment_service.execute_enrichment(
        user_id=current_user.get("id"),
        provider=payload.provider,
        confirm_credits=payload.confirm_credits,
        contact_id=payload.contact_id,
        organization_id=payload.organization_id,
        recruiter_name=payload.recruiter_name,
        company_domain=payload.company_domain
    )
    return EnrichmentRequestOut(
        id=result["id"],
        contact_id=result.get("contact_id"),
        organization_id=result.get("organization_id"),
        provider=result["provider"],
        status=result["status"],
        credits_estimated=1,
        credits_used=result["credits_used"],
        completed_at=result.get("completed_at")
    )

@router.get("/history", response_model=List[EnrichmentRequestOut])
async def get_enrichment_history():
    sql = "SELECT * FROM enrichment_requests ORDER BY created_at DESC LIMIT 50"
    rows = fetch_all(sql)
    return [EnrichmentRequestOut(**r) for r in rows]
