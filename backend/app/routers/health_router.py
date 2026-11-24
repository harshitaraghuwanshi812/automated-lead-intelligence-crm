from fastapi import APIRouter
from app.models.schemas import SystemHealthMetrics
from app.services import health_service

router = APIRouter(prefix="/health", tags=["System Health & Monitoring"])

@router.get("", response_model=SystemHealthMetrics)
async def get_health():
    """Returns comprehensive system health, queue sizes, credit counters, and provider status."""
    return health_service.get_system_health()

@router.get("/ping")
async def ping():
    return {"status": "ok", "service": "lead-intelligence-crm"}
