from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SuppressionCreate, SuppressionOut
from app.repositories import crm_repo
from app.auth.security import get_current_user, require_roles

router = APIRouter(prefix="/suppressions", tags=["Suppression Management"])

@router.get("", response_model=List[SuppressionOut])
async def list_suppressions():
    rows = crm_repo.list_suppressions()
    return [SuppressionOut(**r) for r in rows]

@router.post("", response_model=SuppressionOut)
async def add_suppression(payload: SuppressionCreate, current_user: dict = Depends(require_roles(["campaign_manager", "admin"]))):
    res = crm_repo.add_suppression_entry(
        entity_type=payload.entity_type,
        value=payload.value,
        reason=payload.reason,
        notes=payload.notes,
        user_id=current_user.get("id")
    )
    return SuppressionOut(**res)

@router.get("/check/{value}")
async def check_suppression(value: str):
    is_supp = crm_repo.is_suppressed(value)
    return {"value": value, "is_suppressed": is_supp}
