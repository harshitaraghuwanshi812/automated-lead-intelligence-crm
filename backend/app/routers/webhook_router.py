import logging
from typing import Any, Dict
from fastapi import APIRouter, Request, Header, HTTPException
from app.services import callback_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Provider Callbacks"])

@router.post("/provider")
async def handle_provider_webhook(
    request: Request,
    x_provider_signature: str = Header(None, alias="X-Provider-Signature")
):
    """
    Handles delivery, reply, bounce, and unsubscribe callbacks from email provider.
    Verifies HMAC signature, enforces event idempotency, and updates suppression.
    """
    raw_body = await request.body()
    
    # 1. HMAC verification
    if not callback_service.verify_hmac_signature(raw_body, x_provider_signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC webhook signature")

    # 2. Parse JSON
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # 3. Process event
    result = callback_service.process_provider_event(payload)
    return result

@router.post("/n8n")
async def handle_n8n_webhook(payload: Dict[str, Any]):
    """Receives operational notifications and triggers from self-hosted n8n workflows."""
    logger.info(f"Received webhook trigger from n8n: {payload.get('workflow_name')}")
    return {"status": "received", "workflow": payload.get("workflow_name")}
