import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import HTTPException
from app.config import settings
from app.repositories import crm_repo, campaign_repo
from app.database import fetch_one

logger = logging.getLogger(__name__)

ALLOWED_EVENTS = {"delivered", "open", "click", "bounce", "reply", "unsubscribe"}

def verify_hmac_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """Verifies HMAC SHA256 signature for provider webhook callbacks."""
    if not signature_header:
        # If no secret configured or in local sandbox, allow
        if settings.ENVIRONMENT == "development" or not settings.WEBHOOK_HMAC_SECRET:
            return True
        return False

    expected_sig = hmac.new(
        settings.WEBHOOK_HMAC_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_sig, signature_header)

def process_provider_event(
    event_payload: Dict[str, Any],
    provider: str = "webhook_provider"
) -> Dict[str, Any]:
    """
    Processes delivery callbacks, bounces, replies and unsubscribes with idempotency.
    """
    provider_event_id = event_payload.get("event_id") or event_payload.get("id")
    event_type = event_payload.get("event_type", "").lower()
    recipient = event_payload.get("recipient_email", "").lower()
    provider_message_id = event_payload.get("provider_message_id")

    if not provider_event_id:
        raise HTTPException(status_code=400, detail="Missing required 'event_id' in webhook payload.")

    if event_type not in ALLOWED_EVENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported event type: '{event_type}'.")

    # 1. Event Idempotency check: Ensure event is not processed twice
    existing_evt = fetch_one(
        "SELECT id FROM message_events WHERE provider_event_id = %s LIMIT 1",
        [provider_event_id]
    )
    if existing_evt:
        logger.info(f"Duplicate webhook event ignored: {provider_event_id}")
        return {
            "status": "duplicate_event_ignored",
            "event_id": provider_event_id
        }

    # 2. Find associated outreach message
    msg = None
    if provider_message_id:
        msg = fetch_one("SELECT * FROM outreach_messages WHERE provider_message_id = %s LIMIT 1", [provider_message_id])
    if not msg and recipient:
        msg = fetch_one(
            "SELECT * FROM outreach_messages WHERE LOWER(recipient_email) = %s ORDER BY created_at DESC LIMIT 1",
            [recipient]
        )

    outreach_message_id = msg.get("id") if msg else "00000000-0000-0000-0000-000000000000"

    # 3. Record event in message_events
    record = campaign_repo.record_message_event(
        outreach_message_id=outreach_message_id,
        event_type=event_type,
        provider=provider,
        provider_event_id=provider_event_id,
        event_timestamp=datetime.now(timezone.utc),
        raw_payload=event_payload
    )

    # 4. Handle State Transitions & Guardrails
    if event_type == "bounce":
        # Auto-suppress hard bounce to protect domain reputation
        if recipient and not crm_repo.is_suppressed(recipient):
            crm_repo.add_suppression_entry(
                entity_type="email",
                value=recipient,
                reason="hard_bounce",
                notes=f"Auto-suppressed via callback from provider {provider}"
            )
        if msg:
            campaign_repo.update_outreach_message_status(msg["id"], send_status="bounced")

    elif event_type == "unsubscribe":
        # Auto-suppress opt-out
        if recipient and not crm_repo.is_suppressed(recipient):
            crm_repo.add_suppression_entry(
                entity_type="email",
                value=recipient,
                reason="user_opt_out",
                notes="Recipient clicked unsubscribe link"
            )
        if msg:
            campaign_repo.update_outreach_message_status(msg["id"], send_status="opted_out")

    elif event_type == "reply":
        if msg:
            campaign_repo.update_outreach_message_status(msg["id"], send_status="replied")
            # Cancel subsequent follow-ups (Rule 6 in Section 5)

    elif event_type in ["delivered", "open", "click"]:
        if msg:
            campaign_repo.update_outreach_message_status(msg["id"], send_status=event_type)

    return {
        "status": "processed",
        "event_id": provider_event_id,
        "event_type": event_type,
        "recipient": recipient
    }
