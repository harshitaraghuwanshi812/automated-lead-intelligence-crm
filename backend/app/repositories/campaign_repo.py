import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database import execute_query, fetch_one, fetch_all

def create_campaign(
    name: str,
    description: Optional[str] = None,
    objective: Optional[str] = None,
    daily_limit: int = 50,
    monthly_limit: int = 1000,
    created_by_user_id: Optional[str] = None
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO campaigns (id, name, description, objective, status, daily_limit, monthly_limit, sent_count, created_by_user_id)
    VALUES (%s, %s, %s, %s, 'draft', %s, %s, 0, %s)
    """
    execute_query(sql, [new_id, name, description, objective, daily_limit, monthly_limit, created_by_user_id])
    return fetch_one("SELECT * FROM campaigns WHERE id = %s", [new_id]) or {
        "id": new_id, "name": name, "status": "draft", "daily_limit": daily_limit, "sent_count": 0
    }

def list_campaigns() -> List[Dict[str, Any]]:
    sql = "SELECT * FROM campaigns ORDER BY created_at DESC"
    rows = fetch_all(sql)
    for c in rows:
        c_id = c.get("id")
        drafts = fetch_all("SELECT id, status FROM campaign_drafts WHERE campaign_id = %s", [c_id])
        c["draft_count"] = len(drafts)
        c["approved_count"] = sum(1 for d in drafts if d.get("status") == "approved")
    return rows

def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM campaigns WHERE id = %s"
    return fetch_one(sql, [campaign_id])

def update_campaign_status(campaign_id: str, status: str):
    sql = "UPDATE campaigns SET status = %s, updated_at = (NOW() AT TIME ZONE 'utc') WHERE id = %s"
    execute_query(sql, [status, campaign_id])

def create_campaign_draft(
    campaign_id: str,
    opportunity_id: str,
    contact_id: str,
    subject_line: str,
    email_body: str,
    personalization_summary: str,
    claims_used: List[str],
    missing_info_warnings: List[str],
    confidence_notes: str,
    model_name: str,
    prompt_version: str,
    input_references: Dict[str, Any]
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO campaign_drafts (
        id, campaign_id, opportunity_id, contact_id, subject_line, email_body,
        personalization_summary, claims_used, missing_info_warnings, confidence_notes,
        model_name, prompt_version, input_references, status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [
        new_id, campaign_id, opportunity_id, contact_id, subject_line, email_body,
        personalization_summary, json.dumps(claims_used), json.dumps(missing_info_warnings),
        confidence_notes, model_name, prompt_version, json.dumps(input_references), "generated"
    ])
    return get_campaign_draft(new_id)

def get_campaign_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT cd.*, 
           c.full_name as recipient_name,
           cm.value as recipient_email,
           org.name as company_name,
           opp.title as job_title
    FROM campaign_drafts cd
    LEFT JOIN contacts c ON cd.contact_id = c.id
    LEFT JOIN contact_methods cm ON cm.contact_id = c.id AND cm.is_primary = TRUE
    LEFT JOIN opportunities opp ON cd.opportunity_id = opp.id
    LEFT JOIN organizations org ON opp.organization_id = org.id
    WHERE cd.id = %s
    """
    row = fetch_one(sql, [draft_id])
    if row:
        for k in ["claims_used", "missing_info_warnings", "input_references"]:
            if isinstance(row.get(k), str):
                try:
                    row[k] = json.loads(row[k])
                except Exception:
                    pass
    return row

def update_draft_content(draft_id: str, subject_line: str, email_body: str) -> Optional[Dict[str, Any]]:
    sql = """
    UPDATE campaign_drafts 
    SET subject_line = %s, email_body = %s, status = 'edited', updated_at = (NOW() AT TIME ZONE 'utc')
    WHERE id = %s
    """
    execute_query(sql, [subject_line, email_body, draft_id])
    return get_campaign_draft(draft_id)

def list_campaign_drafts(campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if campaign_id:
        sql = """
        SELECT cd.*, 
               c.full_name as recipient_name,
               cm.value as recipient_email,
               org.name as company_name,
               opp.title as job_title
        FROM campaign_drafts cd
        LEFT JOIN contacts c ON cd.contact_id = c.id
        LEFT JOIN contact_methods cm ON cm.contact_id = c.id AND cm.is_primary = TRUE
        LEFT JOIN opportunities opp ON cd.opportunity_id = opp.id
        LEFT JOIN organizations org ON opp.organization_id = org.id
        WHERE cd.campaign_id = %s
        ORDER BY cd.created_at DESC
        """
        rows = fetch_all(sql, [campaign_id])
    else:
        sql = """
        SELECT cd.*, 
               c.full_name as recipient_name,
               cm.value as recipient_email,
               org.name as company_name,
               opp.title as job_title
        FROM campaign_drafts cd
        LEFT JOIN contacts c ON cd.contact_id = c.id
        LEFT JOIN contact_methods cm ON cm.contact_id = c.id AND cm.is_primary = TRUE
        LEFT JOIN opportunities opp ON cd.opportunity_id = opp.id
        LEFT JOIN organizations org ON opp.organization_id = org.id
        ORDER BY cd.created_at DESC
        LIMIT 100
        """
        rows = fetch_all(sql)
    for r in rows:
        for k in ["claims_used", "missing_info_warnings"]:
            if isinstance(r.get(k), str):
                try:
                    r[k] = json.loads(r[k])
                except Exception:
                    r[k] = []
    return rows

def create_approval(
    campaign_draft_id: str,
    reviewed_by_user_id: str,
    decision: str,
    review_notes: Optional[str],
    approved_recipient: str,
    approved_subject: str,
    approved_body: str
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO approvals (
        id, campaign_draft_id, reviewed_by_user_id, decision, review_notes,
        approved_recipient, approved_subject, approved_body
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [
        new_id, campaign_draft_id, reviewed_by_user_id, decision, review_notes,
        approved_recipient, approved_subject, approved_body
    ])
    
    # Update draft status
    draft_status = "approved" if decision == "approved" else "rejected"
    execute_query("UPDATE campaign_drafts SET status = %s WHERE id = %s", [draft_status, campaign_draft_id])
    
    return {
        "id": new_id,
        "campaign_draft_id": campaign_draft_id,
        "reviewed_by_user_id": reviewed_by_user_id,
        "decision": decision,
        "review_notes": review_notes,
        "approved_recipient": approved_recipient,
        "approved_subject": approved_subject,
        "approved_body": approved_body
    }

def get_approval_by_draft(draft_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT a.*, u.full_name as reviewer_name 
    FROM approvals a
    LEFT JOIN users u ON a.reviewed_by_user_id = u.id
    WHERE a.campaign_draft_id = %s 
    ORDER BY a.approved_at DESC 
    LIMIT 1
    """
    return fetch_one(sql, [draft_id])

def create_outreach_message(
    campaign_id: str,
    campaign_draft_id: str,
    approval_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    idempotency_key: str,
    provider: str = "mock"
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO outreach_messages (
        id, campaign_id, campaign_draft_id, approval_id, recipient_email,
        subject, body, idempotency_key, provider, send_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """
    execute_query(sql, [
        new_id, campaign_id, campaign_draft_id, approval_id, recipient_email,
        subject, body, idempotency_key, provider
    ])
    return fetch_one("SELECT * FROM outreach_messages WHERE id = %s", [new_id]) or {
        "id": new_id, "campaign_id": campaign_id, "recipient_email": recipient_email,
        "idempotency_key": idempotency_key, "send_status": "pending"
    }

def get_outreach_message_by_idempotency(idempotency_key: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM outreach_messages WHERE idempotency_key = %s"
    return fetch_one(sql, [idempotency_key])

def update_outreach_message_status(
    message_id: str,
    send_status: str,
    provider_message_id: Optional[str] = None,
    error_message: Optional[str] = None
):
    sql = """
    UPDATE outreach_messages 
    SET send_status = %s, provider_message_id = %s, error_message = %s,
        sent_at = CASE WHEN %s IN ('sent', 'delivered') THEN (NOW() AT TIME ZONE 'utc') ELSE sent_at END
    WHERE id = %s
    """
    execute_query(sql, [send_status, provider_message_id, error_message, send_status, message_id])

def record_message_event(
    outreach_message_id: str,
    event_type: str,
    provider: str,
    provider_event_id: str,
    event_timestamp: datetime,
    raw_payload: Dict[str, Any]
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO message_events (
        id, outreach_message_id, event_type, provider, provider_event_id,
        event_timestamp, raw_payload
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [
        new_id, outreach_message_id, event_type, provider, provider_event_id,
        event_timestamp.isoformat(), json.dumps(raw_payload)
    ])
    return {"id": new_id, "event_type": event_type, "provider_event_id": provider_event_id}

def get_sent_counts_today(campaign_id: Optional[str] = None) -> int:
    sql = "SELECT COUNT(*) as count FROM outreach_messages WHERE send_status IN ('sent', 'delivered') AND sent_at >= CURRENT_DATE"
    res = fetch_one(sql)
    return res.get("count", 0) if res else 0

def increment_campaign_sent_count(campaign_id: str):
    sql = "UPDATE campaigns SET sent_count = sent_count + 1 WHERE id = %s"
    execute_query(sql, [campaign_id])
