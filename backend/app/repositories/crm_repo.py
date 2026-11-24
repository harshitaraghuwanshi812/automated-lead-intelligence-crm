import json
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database import execute_query, fetch_one, fetch_all, get_db_connection

def normalize_text(text: str) -> str:
    """Normalize organization name or text for deduplication."""
    if not text:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    # remove common suffixes
    cleaned = re.sub(r'\b(inc|corp|corporation|ltd|limited|llc|technologies|solutions|pvt)\b', '', cleaned)
    return ' '.join(cleaned.split())

# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

def get_or_create_organization(
    name: str,
    domain: Optional[str] = None,
    industry: Optional[str] = None,
    website_url: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    norm_name = normalize_text(name)
    sql_check = "SELECT * FROM organizations WHERE normalized_name = %s LIMIT 1"
    existing = fetch_one(sql_check, [norm_name])
    if existing:
        return existing

    new_id = str(uuid.uuid4())
    sql_insert = """
    INSERT INTO organizations (id, name, normalized_name, domain, industry, website_url, location)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql_insert, [new_id, name, norm_name, domain, industry, website_url, location])
    return fetch_one("SELECT * FROM organizations WHERE id = %s", [new_id]) or {
        "id": new_id, "name": name, "normalized_name": norm_name, "domain": domain, "industry": industry
    }

def list_organizations(search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM organizations ORDER BY created_at DESC LIMIT 100"
    return fetch_all(sql)

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def list_approved_sources() -> List[Dict[str, Any]]:
    sql = "SELECT * FROM sources WHERE is_approved = TRUE ORDER BY reliability_weight DESC"
    return fetch_all(sql)

def get_or_create_source(name: str, base_url: str, source_type: str = "job_board", reliability_weight: int = 20) -> Dict[str, Any]:
    existing = fetch_one("SELECT * FROM sources WHERE name = %s LIMIT 1", [name])
    if existing:
        return existing
    new_id = str(uuid.uuid4())
    sql_insert = """
    INSERT INTO sources (id, name, base_url, source_type, reliability_weight, is_approved)
    VALUES (%s, %s, %s, %s, %s, TRUE)
    """
    execute_query(sql_insert, [new_id, name, base_url, source_type, reliability_weight])
    return fetch_one("SELECT * FROM sources WHERE id = %s", [new_id]) or {
        "id": new_id, "name": name, "base_url": base_url, "reliability_weight": reliability_weight
    }

# ---------------------------------------------------------------------------
# Opportunities & Deduplication
# ---------------------------------------------------------------------------

def check_opportunity_exists(source_id: Optional[str], source_identifier: Optional[str], title: str, org_id: Optional[str]) -> bool:
    """Check duplicate by (source_id, source_identifier) or normalized title + org."""
    if source_id and source_identifier:
        row = fetch_one("SELECT id FROM opportunities WHERE source_id = %s AND source_identifier = %s", [source_id, source_identifier])
        if row:
            return True
    if org_id and title:
        row = fetch_one("SELECT id FROM opportunities WHERE organization_id = %s AND LOWER(title) = LOWER(%s)", [org_id, title.strip()])
        if row:
            return True
    return False

def create_opportunity_record(
    organization_id: Optional[str],
    title: str,
    description: str,
    opportunity_type: str,
    experience_level: str,
    source_url: str,
    source_id: Optional[str] = None,
    source_identifier: Optional[str] = None,
    location: Optional[str] = None,
    salary_range: Optional[str] = None,
    publication_date: Optional[str] = None,
    confidence_score: int = 0
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO opportunities (
        id, organization_id, title, description, opportunity_type, experience_level,
        location, salary_range, source_id, source_url, source_identifier,
        status, confidence_score, publication_date
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'discovered', %s, %s)
    """
    execute_query(sql, [
        new_id, organization_id, title, description, opportunity_type, experience_level,
        location, salary_range, source_id, source_url, source_identifier,
        confidence_score, publication_date
    ])
    return fetch_one("SELECT * FROM opportunities WHERE id = %s", [new_id]) or {
        "id": new_id, "title": title, "organization_id": organization_id, "status": "discovered"
    }

def list_opportunities(
    experience_level: Optional[str] = None,
    opportunity_type: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: Optional[int] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    sql = """
    SELECT o.*, org.name as organization_name, s.name as source_name
    FROM opportunities o
    LEFT JOIN organizations org ON o.organization_id = org.id
    LEFT JOIN sources s ON o.source_id = s.id
    ORDER BY o.created_at DESC
    LIMIT 200
    """
    rows = fetch_all(sql)
    
    # In-memory filter fallback for rich filtering
    results = []
    for r in rows:
        if experience_level and experience_level != "all":
            if r.get("experience_level") != experience_level:
                continue
        if opportunity_type and opportunity_type != "all":
            if r.get("opportunity_type") != opportunity_type:
                continue
        if status and status != "all":
            if r.get("status") != status:
                continue
        if min_confidence is not None:
            if (r.get("confidence_score") or 0) < min_confidence:
                continue
        if search:
            s_low = search.lower()
            t_match = s_low in r.get("title", "").lower()
            org_match = s_low in (r.get("organization_name") or "").lower()
            loc_match = s_low in (r.get("location") or "").lower()
            if not (t_match or org_match or loc_match):
                continue
        results.append(r)
    return results

def get_opportunity(opp_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT o.*, org.name as organization_name, org.domain as org_domain, s.name as source_name
    FROM opportunities o
    LEFT JOIN organizations org ON o.organization_id = org.id
    LEFT JOIN sources s ON o.source_id = s.id
    WHERE o.id = %s
    """
    return fetch_one(sql, [opp_id])

def update_opportunity_status(opp_id: str, status: str, confidence_score: Optional[int] = None):
    if confidence_score is not None:
        execute_query(
            "UPDATE opportunities SET status = %s, confidence_score = %s, updated_at = (NOW() AT TIME ZONE 'utc') WHERE id = %s",
            [status, confidence_score, opp_id]
        )
    else:
        execute_query(
            "UPDATE opportunities SET status = %s, updated_at = (NOW() AT TIME ZONE 'utc') WHERE id = %s",
            [status, opp_id]
        )

# ---------------------------------------------------------------------------
# Contacts & Methods
# ---------------------------------------------------------------------------

def create_contact(
    organization_id: Optional[str],
    full_name: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role_title: Optional[str] = None,
    department: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    source: str = "official_channel",
    provenance_notes: Optional[str] = None
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO contacts (
        id, organization_id, full_name, first_name, last_name,
        role_title, department, linkedin_url, source, provenance_notes,
        verification_status, confidence_score
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'unknown', 20)
    """
    execute_query(sql, [
        new_id, organization_id, full_name, first_name, last_name,
        role_title, department, linkedin_url, source, provenance_notes
    ])
    return fetch_one("SELECT * FROM contacts WHERE id = %s", [new_id]) or {
        "id": new_id, "full_name": full_name, "organization_id": organization_id
    }

def add_contact_method(
    contact_id: str,
    method_type: str,
    value: str,
    is_primary: bool = True,
    verification_status: str = "unknown"
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO contact_methods (id, contact_id, method_type, value, is_primary, verification_status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [new_id, contact_id, method_type, value, is_primary, verification_status])
    return fetch_one("SELECT * FROM contact_methods WHERE id = %s", [new_id]) or {
        "id": new_id, "contact_id": contact_id, "method_type": method_type, "value": value
    }

def link_opportunity_contact(opportunity_id: str, contact_id: str, role_in_opportunity: str = "recruiter", association_confidence: int = 20):
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO opportunity_contacts (id, opportunity_id, contact_id, role_in_opportunity, association_confidence)
    VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(sql, [new_id, opportunity_id, contact_id, role_in_opportunity, association_confidence])

def get_contacts_for_opportunity(opp_id: str) -> List[Dict[str, Any]]:
    sql = """
    SELECT c.*, oc.role_in_opportunity, oc.association_confidence,
           cm.value as email, cm.verification_status as email_verification_status
    FROM opportunity_contacts oc
    JOIN contacts c ON oc.contact_id = c.id
    LEFT JOIN contact_methods cm ON cm.contact_id = c.id AND cm.is_primary = TRUE
    WHERE oc.opportunity_id = %s
    """
    return fetch_all(sql, [opp_id])

def list_contacts(search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = """
    SELECT c.*, org.name as organization_name,
           cm.value as email, cm.verification_status as email_status
    FROM contacts c
    LEFT JOIN organizations org ON c.organization_id = org.id
    LEFT JOIN contact_methods cm ON cm.contact_id = c.id AND cm.is_primary = TRUE
    ORDER BY c.created_at DESC
    LIMIT 200
    """
    return fetch_all(sql)

# ---------------------------------------------------------------------------
# Data Quality Scores
# ---------------------------------------------------------------------------

def save_data_quality_score(
    entity_type: str,
    entity_id: str,
    total_score: int,
    source_reliability_score: int,
    org_association_score: int,
    verification_evidence_score: int,
    data_freshness_score: int,
    completeness_score: int,
    score_band: str,
    reason_codes: List[str],
    scoring_version: str = "v1.0.0"
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO data_quality_scores (
        id, entity_type, entity_id, total_score,
        source_reliability_score, org_association_score, verification_evidence_score,
        data_freshness_score, completeness_score, score_band, reason_codes, scoring_version
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [
        new_id, entity_type, entity_id, total_score,
        source_reliability_score, org_association_score, verification_evidence_score,
        data_freshness_score, completeness_score, score_band, json.dumps(reason_codes), scoring_version
    ])
    return {
        "id": new_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total_score": total_score,
        "source_reliability_score": source_reliability_score,
        "org_association_score": org_association_score,
        "verification_evidence_score": verification_evidence_score,
        "data_freshness_score": data_freshness_score,
        "completeness_score": completeness_score,
        "score_band": score_band,
        "reason_codes": reason_codes,
        "scoring_version": scoring_version
    }

def get_latest_quality_score(entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT * FROM data_quality_scores
    WHERE entity_type = %s AND entity_id = %s
    ORDER BY scored_at DESC
    LIMIT 1
    """
    row = fetch_one(sql, [entity_type, entity_id])
    if row and isinstance(row.get("reason_codes"), str):
        try:
            row["reason_codes"] = json.loads(row["reason_codes"])
        except Exception:
            row["reason_codes"] = []
    return row

# ---------------------------------------------------------------------------
# Suppression Check
# ---------------------------------------------------------------------------

def is_suppressed(email_or_domain: str) -> bool:
    if not email_or_domain:
        return False
    val = email_or_domain.strip().lower()
    row = fetch_one("SELECT id FROM suppression_entries WHERE LOWER(value) = %s LIMIT 1", [val])
    if row:
        return True
    if "@" in val:
        domain = val.split("@")[-1]
        dom_row = fetch_one("SELECT id FROM suppression_entries WHERE LOWER(value) = %s LIMIT 1", [domain])
        if dom_row:
            return True
    return False

def add_suppression_entry(entity_type: str, value: str, reason: str, notes: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    val = value.strip().lower()
    sql = """
    INSERT INTO suppression_entries (id, entity_type, value, reason, notes, suppressed_by_user_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [new_id, entity_type, val, reason, notes, user_id])
    return {"id": new_id, "entity_type": entity_type, "value": val, "reason": reason, "notes": notes}

def list_suppressions() -> List[Dict[str, Any]]:
    sql = "SELECT * FROM suppression_entries ORDER BY created_at DESC"
    return fetch_all(sql)

# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

def log_audit(user_id: Optional[str], action: str, entity_type: str, entity_id: Optional[str], details: Dict[str, Any] = None, ip_address: Optional[str] = None):
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(sql, [new_id, user_id, action, entity_type, entity_id, json.dumps(details or {}), ip_address])
