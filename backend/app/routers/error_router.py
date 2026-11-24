from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import AutomationErrorOut, ErrorRetryRequest
from app.repositories import error_repo
from app.services import error_service
from app.auth.security import get_current_user, require_roles

router = APIRouter(prefix="/errors", tags=["Error Center"])

@router.get("", response_model=List[AutomationErrorOut])
async def list_errors(
    recovery_status: Optional[str] = Query(None, description="unresolved, retrying, resolved, quarantined"),
    failure_category: Optional[str] = Query(None, description="network, rate_limit, validation, credential, credit_exhaustion, source_layout, ai_output, send_timeout, provider_rejection")
):
    rows = error_repo.list_automation_errors(
        recovery_status=recovery_status,
        failure_category=failure_category
    )
    return [AutomationErrorOut(**r) for r in rows]

@router.get("/{error_id}", response_model=AutomationErrorOut)
async def get_error(error_id: str):
    err = error_repo.get_automation_error(error_id)
    if not err:
        raise HTTPException(status_code=404, detail="Error record not found")
    return AutomationErrorOut(**err)

@router.post("/{error_id}/retry")
async def retry_error(
    error_id: str,
    payload: Optional[ErrorRetryRequest] = None,
    current_user: dict = Depends(require_roles(["admin", "campaign_manager"]))
):
    """
    Manually retries eligible failed automation task with exponential backoff & jitter.
    """
    notes = payload.resolution_notes if payload else None
    res = error_service.retry_failed_job(
        error_id=error_id,
        user_id=current_user.get("id"),
        resolution_notes=notes
    )
    return res
