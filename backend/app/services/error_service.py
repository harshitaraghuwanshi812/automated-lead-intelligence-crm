import math
import random
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.repositories import error_repo, crm_repo

logger = logging.getLogger(__name__)

FAILURE_CATEGORIES = [
    "network",
    "rate_limit",
    "validation",
    "credential",
    "credit_exhaustion",
    "source_layout",
    "ai_output",
    "send_timeout",
    "provider_rejection"
]

def calculate_backoff_seconds(retry_count: int, base_seconds: int = 5, max_seconds: int = 300) -> int:
    """Bounded exponential backoff with random jitter."""
    exp = min(retry_count, 5)
    delay = base_seconds * (2 ** exp)
    jitter = random.uniform(0.8, 1.2)
    return min(int(delay * jitter), max_seconds)

def capture_automation_error(
    workflow_name: str,
    failed_step: str,
    failure_category: str,
    error_message: str,
    correlation_id: Optional[str] = None,
    job_id: Optional[str] = None,
    stack_trace: Optional[str] = None
) -> Dict[str, Any]:
    """Captures and categorizes automation failure according to PRD Section 11."""
    corr_id = correlation_id or f"corr_{uuid.uuid4().hex[:12]}"
    
    # Check replay eligibility based on category
    # Never replay validation errors or credit exhaustion blindly
    is_replay_eligible = failure_category in [
        "network", "rate_limit", "send_timeout", "ai_output"
    ]

    err = error_repo.record_automation_error(
        job_id=job_id,
        correlation_id=corr_id,
        workflow_name=workflow_name,
        failed_step=failed_step,
        failure_category=failure_category,
        error_message=error_message,
        stack_trace=stack_trace,
        is_replay_eligible=is_replay_eligible
    )

    logger.warning(
        f"Automation error logged: [{failure_category}] {workflow_name} - {failed_step}: {error_message} (CorrID: {corr_id})"
    )

    return err

def retry_failed_job(error_id: str, user_id: str, resolution_notes: Optional[str] = None) -> Dict[str, Any]:
    """Manual retry trigger from Error Center UI."""
    err = error_repo.get_automation_error(error_id)
    if not err:
        raise HTTPException(status_code=404, detail="Error record not found")

    if not err.get("is_replay_eligible"):
        raise HTTPException(
            status_code=400,
            detail=f"This error of category '{err.get('failure_category')}' is not eligible for automated replay. Manual remediation required."
        )

    # Calculate backoff
    retries = err.get("retry_count", 0) + 1
    backoff = calculate_backoff_seconds(retries)
    next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff)

    notes = resolution_notes or f"Manual retry initiated by user. Scheduled after {backoff}s backoff."
    error_repo.resolve_automation_error(error_id, resolution_notes=notes, new_status="retrying")

    crm_repo.log_audit(
        user_id=user_id,
        action="ERROR_RETRY_TRIGGERED",
        entity_type="automation_error",
        entity_id=error_id,
        details={"retry_count": retries, "category": err.get("failure_category")}
    )

    return {
        "status": "retry_scheduled",
        "error_id": error_id,
        "retry_count": retries,
        "next_retry_at": next_retry.isoformat(),
        "resolution_notes": notes
    }
