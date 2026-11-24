from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SourceCreate, SourceOut
from app.repositories import crm_repo
from app.services import discovery_service
from app.auth.security import get_current_user, require_roles

router = APIRouter(prefix="/discovery", tags=["Lead Discovery"])

@router.get("/sources", response_model=List[SourceOut])
async def list_sources():
    sources = crm_repo.list_approved_sources()
    return [SourceOut(**s) for s in sources]

@router.post("/sources", response_model=SourceOut)
async def create_source(payload: SourceCreate, current_user: dict = Depends(require_roles(["admin"]))):
    src = crm_repo.get_or_create_source(
        name=payload.name,
        base_url=payload.base_url,
        source_type=payload.source_type,
        reliability_weight=payload.reliability_weight
    )
    return SourceOut(**src)

@router.post("/ingest")
async def ingest_lead(raw_lead: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Ingests discovered opportunity from Playwright worker or n8n scheduler."""
    result = discovery_service.process_discovered_lead(
        raw_lead=raw_lead,
        source_name=raw_lead.get("source_name", "Approved Career Platform")
    )
    return result

@router.post("/ingest-batch")
async def ingest_lead_batch(batch: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    created = 0
    duplicates = 0
    for lead in batch:
        res = discovery_service.process_discovered_lead(lead, lead.get("source_name", "Approved Source"))
        if res.get("status") == "created":
            created += 1
        elif res.get("status") == "duplicate_skipped":
            duplicates += 1
    return {
        "total_processed": len(batch),
        "created": created,
        "duplicates_skipped": duplicates
    }
