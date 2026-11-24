import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, close_db
try:
    from migrations.seed_data import seed_database
except ImportError:
    from app.migrations.seed_data import seed_database
from app.routers import (
    auth_router,
    crm_router,
    discovery_router,
    enrichment_router,
    verification_router,
    scoring_router,
    campaign_router,
    suppression_router,
    error_router,
    health_router,
    webhook_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lead_intelligence_crm")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(">>> ENTERING LIFESPAN", flush=True)
    init_db()
    try:
        print(">>> SEEDING DATABASE", flush=True)
        seed_database()
        print(">>> SEEDED DATABASE", flush=True)
    except Exception as e:
        logger.warning(f"Seed execution note: {e}")
    print(">>> YIELDING IN LIFESPAN", flush=True)
    yield
    # Shutdown
    print(">>> EXITING LIFESPAN", flush=True)
    close_db()

app = FastAPI(
    title="Automated Lead Generation & Outreach System",
    description="AI-Powered Lead Intelligence, CRM & Outreach Automation Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Cloudflare Pages and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", # Allow all for API consumers and Cloudflare Pages previews
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all documented API v1 Routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(crm_router.router, prefix="/api/v1")
app.include_router(discovery_router.router, prefix="/api/v1")
app.include_router(enrichment_router.router, prefix="/api/v1")
app.include_router(verification_router.router, prefix="/api/v1")
app.include_router(scoring_router.router, prefix="/api/v1")
app.include_router(campaign_router.router, prefix="/api/v1")
app.include_router(suppression_router.router, prefix="/api/v1")
app.include_router(error_router.router, prefix="/api/v1")
app.include_router(health_router.router, prefix="/api/v1")
app.include_router(webhook_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "system": "Automated Lead Generation & Outreach System",
        "subtitle": "AI-Powered Lead Intelligence, CRM & Outreach Automation",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
