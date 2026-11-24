from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import OrganizationCreate, OrganizationOut, OpportunityCreate, OpportunityOut, ContactCreate, ContactOut
from app.repositories import crm_repo
from app.services import discovery_service, scoring_service
from app.auth.security import get_current_user

router = APIRouter(prefix="/crm", tags=["CRM Core"])

# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

@router.get("/organizations", response_model=List[OrganizationOut])
async def get_organizations(search: Optional[str] = None):
    rows = crm_repo.list_organizations(search=search)
    return [OrganizationOut(**r) for r in rows]

@router.post("/organizations", response_model=OrganizationOut)
async def create_organization(payload: OrganizationCreate, current_user: dict = Depends(get_current_user)):
    org = crm_repo.get_or_create_organization(
        name=payload.name,
        domain=payload.domain,
        industry=payload.industry,
        website_url=payload.website_url,
        location=payload.location
    )
    return OrganizationOut(**org)

# ---------------------------------------------------------------------------
# Opportunities & Lead Pipeline
# ---------------------------------------------------------------------------

@router.get("/opportunities", response_model=List[OpportunityOut])
async def get_opportunities(
    experience_level: Optional[str] = Query(None, description="fresher, no_experience, 0-1_year, 0-2_years"),
    opportunity_type: Optional[str] = Query(None, description="job, internship, hackathon, startup"),
    status: Optional[str] = Query(None, description="discovered, reviewed, enrichment_pending, ready_for_draft"),
    min_confidence: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None)
):
    rows = crm_repo.list_opportunities(
        experience_level=experience_level,
        opportunity_type=opportunity_type,
        status=status,
        min_confidence=min_confidence,
        search=search
    )
    
    # Enrich with primary contact status if available
    out = []
    for r in rows:
        contacts = crm_repo.get_contacts_for_opportunity(r["id"])
        c_count = len(contacts)
        p_email = contacts[0].get("email") if contacts else None
        p_status = contacts[0].get("email_verification_status") if contacts else None

        item = dict(r)
        item["contact_count"] = c_count
        item["primary_contact_email"] = p_email
        item["primary_contact_status"] = p_status
        out.append(OpportunityOut(**item))
    return out

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
async def get_opportunity_details(opportunity_id: str):
    opp = crm_repo.get_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    contacts = crm_repo.get_contacts_for_opportunity(opportunity_id)
    item = dict(opp)
    item["contact_count"] = len(contacts)
    item["primary_contact_email"] = contacts[0].get("email") if contacts else None
    item["primary_contact_status"] = contacts[0].get("email_verification_status") if contacts else None
    return OpportunityOut(**item)

@router.post("/opportunities", response_model=OpportunityOut)
async def create_opportunity(payload: OpportunityCreate, current_user: dict = Depends(get_current_user)):
    res = discovery_service.process_discovered_lead(
        raw_lead=payload.model_dump(),
        source_name=payload.source_name or "Direct Input"
    )
    if res.get("status") == "duplicate_skipped":
        raise HTTPException(status_code=409, detail="Opportunity duplicate detected: already exists from this source.")
    
    opp = res["opportunity"]
    return OpportunityOut(
        id=opp["id"],
        organization_id=opp.get("organization_id"),
        organization_name=payload.organization_name,
        title=opp["title"],
        description=opp["description"],
        opportunity_type=opp["opportunity_type"],
        experience_level=opp["experience_level"],
        location=opp.get("location"),
        salary_range=opp.get("salary_range"),
        source_url=opp["source_url"],
        status=opp.get("status", "discovered"),
        confidence_score=opp.get("confidence_score", 0)
    )

# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

@router.get("/contacts", response_model=List[ContactOut])
async def get_contacts(search: Optional[str] = None):
    rows = crm_repo.list_contacts(search=search)
    return [ContactOut(**r) for r in rows]

@router.post("/contacts", response_model=ContactOut)
async def create_contact(payload: ContactCreate, current_user: dict = Depends(get_current_user)):
    org_id = payload.organization_id
    if not org_id and payload.organization_name:
        org = crm_repo.get_or_create_organization(payload.organization_name)
        org_id = org["id"]

    contact = crm_repo.create_contact(
        organization_id=org_id,
        full_name=payload.full_name,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_title=payload.role_title,
        department=payload.department,
        linkedin_url=payload.linkedin_url,
        source=payload.source,
        provenance_notes=payload.provenance_notes
    )

    primary_email = None
    for method in payload.methods:
        cm = crm_repo.add_contact_method(
            contact_id=contact["id"],
            method_type=method.method_type,
            value=method.value,
            is_primary=method.is_primary
        )
        if method.is_primary and method.method_type == "email":
            primary_email = method.value

    return ContactOut(
        id=contact["id"],
        organization_id=org_id,
        full_name=contact["full_name"],
        first_name=contact.get("first_name"),
        last_name=contact.get("last_name"),
        role_title=contact.get("role_title"),
        department=contact.get("department"),
        linkedin_url=contact.get("linkedin_url"),
        source=contact.get("source", "official_channel"),
        provenance_notes=contact.get("provenance_notes"),
        verification_status="unknown",
        confidence_score=20,
        is_suppressed=False,
        email=primary_email
    )
