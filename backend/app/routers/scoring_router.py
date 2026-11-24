from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import QualityScoreOut
from app.services import scoring_service
from app.repositories import crm_repo
from app.auth.security import get_current_user

router = APIRouter(prefix="/scoring", tags=["Data Quality & Confidence Scoring"])

@router.post("/evaluate/{opportunity_id}", response_model=QualityScoreOut)
async def evaluate_confidence(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    """
    Evaluates 5-factor confidence score for an opportunity:
    Source (25) + Org/Contact (25) + Verification (20) + Freshness (15) + Completeness (15) = 100 max.
    """
    score = scoring_service.evaluate_opportunity_confidence(opportunity_id)
    return QualityScoreOut(**score)

@router.get("/latest/{opportunity_id}", response_model=QualityScoreOut)
async def get_latest_score(opportunity_id: str):
    score = crm_repo.get_latest_quality_score("opportunity", opportunity_id)
    if not score:
        # Calculate if not yet evaluated
        score = scoring_service.evaluate_opportunity_confidence(opportunity_id)
    return QualityScoreOut(**score)
