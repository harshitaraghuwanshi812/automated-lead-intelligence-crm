from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from app.models.schemas import (
    CampaignCreate, CampaignOut, DraftGenerateRequest, DraftEditRequest,
    CampaignDraftOut, ApprovalRequest, ApprovalOut, DispatchTriggerRequest, OutreachMessageOut
)
from app.repositories import campaign_repo, crm_repo
from app.services import gemini_service, dispatch_service
from app.auth.security import get_current_user, require_roles

router = APIRouter(prefix="/campaigns", tags=["Campaign Manager & Outreach"])

@router.get("", response_model=List[CampaignOut])
async def list_campaigns():
    camps = campaign_repo.list_campaigns()
    return [CampaignOut(**c) for c in camps]

@router.post("", response_model=CampaignOut)
async def create_campaign(payload: CampaignCreate, current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))):
    camp = campaign_repo.create_campaign(
        name=payload.name,
        description=payload.description,
        objective=payload.objective,
        daily_limit=payload.daily_limit,
        monthly_limit=payload.monthly_limit,
        created_by_user_id=current_user.get("id")
    )
    return CampaignOut(**camp)

@router.patch("/{campaign_id}/status")
async def update_status(
    campaign_id: str,
    status: str = Body(..., embed=True),
    current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))
):
    if status not in ["draft", "active", "paused", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be draft, active, paused, or completed.")
    campaign_repo.update_campaign_status(campaign_id, status)
    return {"id": campaign_id, "status": status}

@router.get("/drafts", response_model=List[CampaignDraftOut])
async def list_drafts(campaign_id: Optional[str] = None):
    drafts = campaign_repo.list_campaign_drafts(campaign_id)
    return [CampaignDraftOut(**d) for d in drafts]

@router.post("/drafts/generate", response_model=CampaignDraftOut)
async def generate_draft(
    payload: DraftGenerateRequest,
    current_user: dict = Depends(require_roles(["campaign_manager", "researcher", "admin"]))
):
    """Generates structured email draft using Gemini Flash with zero hallucination constraints."""
    draft = gemini_service.generate_draft_with_gemini(
        campaign_id=payload.campaign_id,
        opportunity_id=payload.opportunity_id,
        contact_id=payload.contact_id,
        tone=payload.tone or "professional_enthusiastic",
        campaign_objective=payload.campaign_objective
    )
    return CampaignDraftOut(**draft)

@router.get("/drafts/{draft_id}", response_model=CampaignDraftOut)
async def get_draft(draft_id: str):
    draft = campaign_repo.get_campaign_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Campaign draft not found")
    return CampaignDraftOut(**draft)

@router.put("/drafts/{draft_id}", response_model=CampaignDraftOut)
async def edit_draft(
    draft_id: str,
    payload: DraftEditRequest,
    current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))
):
    """Allows Campaign Manager to edit subject line or email body prior to approval."""
    updated = campaign_repo.update_draft_content(
        draft_id=draft_id,
        subject_line=payload.subject_line,
        email_body=payload.email_body
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Campaign draft not found")
    return CampaignDraftOut(**updated)

@router.post("/drafts/{draft_id}/approve", response_model=ApprovalOut)
async def approve_draft(
    draft_id: str,
    payload: ApprovalRequest,
    current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))
):
    """
    MANDATORY Human-in-the-loop approval step.
    Campaign Manager approves exact recipient, subject, and body before sending is unlocked.
    """
    draft = campaign_repo.get_campaign_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Campaign draft not found")

    recip = payload.approved_recipient or draft.get("recipient_email")
    if not recip:
        raise HTTPException(status_code=400, detail="Recipient email must be specified.")

    approval = campaign_repo.create_approval(
        campaign_draft_id=draft_id,
        reviewed_by_user_id=current_user.get("id"),
        decision=payload.decision,
        review_notes=payload.review_notes,
        approved_recipient=recip,
        approved_subject=payload.approved_subject or draft["subject_line"],
        approved_body=payload.approved_body or draft["email_body"]
    )
    approval["reviewer_name"] = current_user.get("full_name", "Campaign Manager")
    return ApprovalOut(**approval)

@router.post("/drafts/{draft_id}/dispatch")
async def dispatch_message(
    draft_id: str,
    payload: Optional[DispatchTriggerRequest] = None,
    current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))
):
    """
    Executes the 7 pre-send checks and dispatches email.
    Blocked unless Human Approval exists.
    """
    idemp_key = payload.idempotency_key if payload else None
    result = dispatch_service.execute_safe_dispatch(
        campaign_draft_id=draft_id,
        user_id=current_user.get("id"),
        custom_idempotency_key=idemp_key
    )
    return result
