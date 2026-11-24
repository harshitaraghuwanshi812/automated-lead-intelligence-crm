import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple
from app.repositories import crm_repo

logger = logging.getLogger(__name__)

def evaluate_opportunity_confidence(opportunity_id: str) -> Dict[str, Any]:
    """
    Implements the exact 5-factor scoring model from Section 9 of the PRD.
    Max 100 points:
      1. Source reliability (25)
      2. Organization and contact association (25)
      3. Contact verification evidence (20)
      4. Data freshness (15)
      5. Completeness and consistency (15)
    """
    opp = crm_repo.get_opportunity(opportunity_id)
    if not opp:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    contacts = crm_repo.get_contacts_for_opportunity(opportunity_id)
    primary_contact = contacts[0] if contacts else None

    # Check suppression first
    recipient_email = primary_contact.get("email") if primary_contact else None
    org_domain = opp.get("org_domain")
    
    is_entity_suppressed = False
    if recipient_email and crm_repo.is_suppressed(recipient_email):
        is_entity_suppressed = True
    elif org_domain and crm_repo.is_suppressed(org_domain):
        is_entity_suppressed = True

    reason_codes: List[str] = []

    # Factor 1: Source Reliability (Max 25)
    source_reliability_score = 0
    source_name = opp.get("source_name", "").lower()
    source_url = opp.get("source_url", "").lower()
    if "official" in source_name or "careers" in source_url or "greenhouse.io" in source_url or "lever.co" in source_url:
        source_reliability_score = 25
        reason_codes.append("OFFICIAL_COMPANY_SOURCE")
    elif "hackathon" in source_name or "unstop" in source_url or "devpost" in source_url:
        source_reliability_score = 22
        reason_codes.append("VERIFIED_EVENT_PLATFORM")
    elif opp.get("source_id"):
        source_reliability_score = 20
        reason_codes.append("APPROVED_JOB_BOARD_SOURCE")
    else:
        source_reliability_score = 10
        reason_codes.append("UNVERIFIED_SOURCE_ORIGIN")

    # Factor 2: Organization and Contact Association (Max 25)
    org_association_score = 0
    if primary_contact:
        role_title = (primary_contact.get("role_title") or "").lower()
        if any(r in role_title for r in ["recruiter", "talent", "hr", "hiring", "head of", "talent acquisition"]):
            org_association_score = 25
            reason_codes.append("CONTACT_ROLE_CONFIRMED")
        elif primary_contact.get("full_name"):
            org_association_score = 18
            reason_codes.append("CONTACT_ASSOCIATED_WITH_ORGANIZATION")
        else:
            org_association_score = 10
            reason_codes.append("CONTACT_COMPANY_ASSOCIATION_UNCONFIRMED")
    else:
        org_association_score = 5
        reason_codes.append("NO_RECRUITER_CONTACT_LINKED")

    # Factor 3: Contact Verification Evidence (Max 20)
    verification_evidence_score = 0
    if primary_contact and recipient_email:
        status = primary_contact.get("email_verification_status", "unknown")
        if status == "deliverable":
            verification_evidence_score = 20
            reason_codes.append("EMAIL_VERIFIED_DELIVERABLE")
        elif status in ["catch-all", "risky"]:
            verification_evidence_score = 10
            reason_codes.append("EMAIL_VERIFIED_RISKY_OR_CATCHALL")
        elif status == "undeliverable":
            verification_evidence_score = 0
            reason_codes.append("EMAIL_UNDELIVERABLE_BOUNCE_RISK")
        else:
            verification_evidence_score = 5
            reason_codes.append("EMAIL_UNVERIFIED_PENDING_CHECK")
    else:
        verification_evidence_score = 0
        reason_codes.append("NO_CONTACT_EMAIL_AVAILABLE")

    # Factor 4: Data Freshness (Max 15)
    data_freshness_score = 0
    pub_date_str = opp.get("publication_date") or opp.get("discovered_at")
    if pub_date_str:
        try:
            # Parse ISO date
            if isinstance(pub_date_str, datetime):
                pub_date = pub_date_str
            else:
                pub_date = datetime.fromisoformat(str(pub_date_str).replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - pub_date).days
            if age_days <= 3:
                data_freshness_score = 15
                reason_codes.append("RECENT_PUBLICATION_VERY_FRESH")
            elif age_days <= 14:
                data_freshness_score = 12
                reason_codes.append("RECENT_PUBLICATION_MODERATE_FRESH")
            elif age_days <= 30:
                data_freshness_score = 8
                reason_codes.append("OLDER_PUBLICATION_ACTIVE")
            else:
                data_freshness_score = 4
                reason_codes.append("STALE_PUBLICATION_OVER_30_DAYS")
        except Exception:
            data_freshness_score = 7
            reason_codes.append("PUBLICATION_DATE_PARSE_FALLBACK")
    else:
        data_freshness_score = 5
        reason_codes.append("PUBLICATION_DATE_MISSING")

    # Factor 5: Completeness and Consistency (Max 15)
    completeness_score = 0
    title = opp.get("title")
    desc = opp.get("description")
    location = opp.get("location")
    exp_level = opp.get("experience_level")

    completeness_pts = 0
    if title and len(title) > 3:
        completeness_pts += 3
    if desc and len(desc) > 50:
        completeness_pts += 4
    if location:
        completeness_pts += 3
    if exp_level and exp_level != "other":
        completeness_pts += 5
        reason_codes.append("EXPERIENCE_REQUIREMENT_MATCH")

    completeness_score = min(15, completeness_pts)
    if completeness_score >= 12:
        reason_codes.append("COMPLETE_DETAILS_PROVIDED")

    # Total Score Calculation
    total_score = (
        source_reliability_score +
        org_association_score +
        verification_evidence_score +
        data_freshness_score +
        completeness_score
    )

    # Determine Band
    if is_entity_suppressed:
        score_band = "suppressed"
        reason_codes.insert(0, "SUPPRESSED_RECIPIENT_OR_DOMAIN")
    elif total_score >= 80:
        score_band = "high_confidence"
    elif total_score >= 60:
        score_band = "medium_confidence"
    else:
        score_band = "low_confidence"

    # Save to database
    score_record = crm_repo.save_data_quality_score(
        entity_type="opportunity",
        entity_id=opportunity_id,
        total_score=total_score,
        source_reliability_score=source_reliability_score,
        org_association_score=org_association_score,
        verification_evidence_score=verification_evidence_score,
        data_freshness_score=data_freshness_score,
        completeness_score=completeness_score,
        score_band=score_band,
        reason_codes=reason_codes
    )

    # Update opportunity with score
    crm_repo.update_opportunity_status(
        opp_id=opportunity_id,
        status="ready_for_draft" if score_band == "high_confidence" else "reviewed",
        confidence_score=total_score
    )

    return score_record
