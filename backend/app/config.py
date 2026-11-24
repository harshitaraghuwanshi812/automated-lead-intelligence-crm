import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: Optional[str] = None
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 10
    DB_TIMEOUT_SECONDS: int = 30

    # Security
    SECRET_KEY: str = "super-secret-development-key-32-chars-long-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    GEMINI_PROMPT_VERSION: str = "v1.0.0"

    # Enrichment
    CONTACTOUT_API_KEY: Optional[str] = None
    SNOVIO_API_USER_ID: Optional[str] = None
    SNOVIO_API_SECRET: Optional[str] = None
    ENRICHMENT_DAILY_CREDIT_BUDGET: int = 50
    ENRICHMENT_MONTHLY_CREDIT_BUDGET: int = 500

    # Verification
    EMAIL_VERIFICATION_PROVIDER: str = "smtp_mx"
    EMAIL_VERIFICATION_API_KEY: Optional[str] = None
    EMAIL_VERIFICATION_DAILY_BUDGET: int = 200

    # Dispatcher
    EMAIL_PROVIDER: str = "mock" # 'mock', 'smtp', 'resend', 'sendgrid'
    EMAIL_API_KEY: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "outreach@leadintel.org"
    EMAIL_FROM_NAME: str = "Lead Outreach Team"
    DAILY_SEND_LIMIT: int = 50
    MONTHLY_SEND_LIMIT: int = 1000

    # Webhook Security
    WEBHOOK_HMAC_SECRET: str = "webhook-hmac-secret-signature-lead-intelligence"

    # n8n Orchestrator
    N8N_BASE_URL: str = "http://n8n:5678"
    N8N_API_KEY: Optional[str] = None

    # Playwright Scraper
    PLAYWRIGHT_CONCURRENCY_LIMIT: int = 2
    SCRAPER_HEADLESS: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
