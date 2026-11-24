import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.repositories import crm_repo

logger = logging.getLogger(__name__)

# Experience levels supported
EXPERIENCE_LEVELS = ["fresher", "no_experience", "0-1_year", "0-2_years", "other"]
OPPORTUNITY_TYPES = ["job", "internship", "hackathon", "startup"]

def generate_source_identifier(source_url: str, title: str, company_name: str) -> str:
    """Generate deterministic hash for opportunity identity and duplicate prevention."""
    raw = f"{source_url.strip().lower()}|{title.strip().lower()}|{company_name.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def classify_experience_level(title: str, description: str) -> str:
    """Classify lead experience requirements according to PRD objectives."""
    combined = f"{title} {description}".lower()
    
    if any(k in combined for k in ["no experience", "0 exp", "zero experience", "without experience"]):
        return "no_experience"
    if any(k in combined for k in ["fresher", "entry level", "entry-level", "college graduate", "campus recruitment", "batch 2024", "batch 2025", "batch 2026", "new grad"]):
        return "fresher"
    if any(k in combined for k in ["0-1 year", "0 to 1 year", "0 - 1 year", "1 year exp", "0-1 yrs", "up to 1 year"]):
        return "0-1_year"
    if any(k in combined for k in ["0-2 year", "0 to 2 year", "0 - 2 year", "1-2 year", "0-2 yrs", "up to 2 years"]):
        return "0-2_years"
    return "fresher" # Default targeted lead category

def classify_opportunity_type(title: str, description: str) -> str:
    combined = f"{title} {description}".lower()
    if any(k in combined for k in ["hackathon", "coding challenge", "ideathon", "codefest"]):
        return "hackathon"
    if any(k in combined for k in ["intern", "internship", "trainee", "apprentice"]):
        return "internship"
    if any(k in combined for k in ["founder", "founding engineer", "startup accelerator", "incubator", "early employee"]):
        return "startup"
    return "job"

def process_discovered_lead(
    raw_lead: Dict[str, Any],
    source_name: str = "Approved Career Source"
) -> Dict[str, Any]:
    """
    Normalizes, deduplicates, and stores an opportunity from an approved source.
    """
    company_name = raw_lead.get("company_name", "Unknown Organization").strip()
    title = raw_lead.get("title", "Untitled Opportunity").strip()
    description = raw_lead.get("description", "No description provided.").strip()
    source_url = raw_lead.get("source_url", "").strip()
    
    if not source_url:
        raise ValueError("source_url is required for lead provenance.")

    # 1. Resolve or create approved Source
    source = crm_repo.get_or_create_source(
        name=source_name,
        base_url=source_url.split("/")[0] + "//" + source_url.split("/")[2] if "://" in source_url else source_url,
        source_type="job_board",
        reliability_weight=20
    )

    # 2. Get or create Organization
    org = crm_repo.get_or_create_organization(
        name=company_name,
        domain=raw_lead.get("domain"),
        location=raw_lead.get("location"),
        website_url=raw_lead.get("website_url")
    )

    # 3. Check for duplicates
    source_identifier = raw_lead.get("source_identifier") or generate_source_identifier(source_url, title, company_name)
    is_duplicate = crm_repo.check_opportunity_exists(
        source_id=source.get("id"),
        source_identifier=source_identifier,
        title=title,
        org_id=org.get("id")
    )

    if is_duplicate:
        logger.info(f"Duplicate opportunity detected and flagged: {title} at {company_name}")
        return {
            "status": "duplicate_skipped",
            "title": title,
            "company_name": company_name,
            "source_identifier": source_identifier
        }

    # 4. Classify filters
    exp_level = raw_lead.get("experience_level") or classify_experience_level(title, description)
    opp_type = raw_lead.get("opportunity_type") or classify_opportunity_type(title, description)

    # 5. Create Opportunity Record
    opp = crm_repo.create_opportunity_record(
        organization_id=org.get("id"),
        title=title,
        description=description,
        opportunity_type=opp_type,
        experience_level=exp_level,
        source_url=source_url,
        source_id=source.get("id"),
        source_identifier=source_identifier,
        location=raw_lead.get("location"),
        salary_range=raw_lead.get("salary_range"),
        publication_date=raw_lead.get("publication_date") or datetime.now(timezone.utc).isoformat(),
        confidence_score=40 # Initial baseline before verification
    )

    # 6. If contact details were discovered, link them
    recruiter_name = raw_lead.get("recruiter_name")
    recruiter_email = raw_lead.get("recruiter_email")
    if recruiter_name or recruiter_email:
        contact = crm_repo.create_contact(
            organization_id=org.get("id"),
            full_name=recruiter_name or f"{company_name} Talent Acquisition",
            role_title=raw_lead.get("recruiter_title", "Talent Acquisition"),
            source="official_channel",
            provenance_notes=f"Extracted from source URL: {source_url}"
        )
        if recruiter_email:
            crm_repo.add_contact_method(
                contact_id=contact.get("id"),
                method_type="email",
                value=recruiter_email,
                is_primary=True,
                verification_status="unknown"
            )
        crm_repo.link_opportunity_contact(
            opportunity_id=opp.get("id"),
            contact_id=contact.get("id"),
            role_in_opportunity="recruiter",
            association_confidence=20
        )

    # 7. Audit log
    crm_repo.log_audit(
        user_id=None,
        action="DISCOVERY_OPPORTUNITY_CREATED",
        entity_type="opportunity",
        entity_id=opp.get("id"),
        details={"title": title, "company": company_name, "source_url": source_url}
    )

    return {
        "status": "created",
        "opportunity": opp,
        "organization": org
    }
