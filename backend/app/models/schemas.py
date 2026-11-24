from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Auth & Roles
# ---------------------------------------------------------------------------

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role_name: str = "researcher" # 'admin', 'researcher', 'campaign_manager'

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    roles: List[str]

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    roles: List[str] = []
    created_at: Optional[str] = None

# ---------------------------------------------------------------------------
# CRM Core: Organizations, Sources, Opportunities, Contacts
# ---------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None

class OrganizationOut(BaseModel):
    id: str
    name: str
    normalized_name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    is_suppressed: bool = False
    created_at: Optional[str] = None

class SourceCreate(BaseModel):
    name: str
    base_url: str
    source_type: str = "job_board" # 'job_board', 'company_careers', 'hackathon_platform', 'recruitment_announcement'
    reliability_weight: int = 20 # 0-25
    is_approved: bool = True
    check_frequency: str = "daily"
    rate_limit_rpm: int = 30

class SourceOut(BaseModel):
    id: str
    name: str
    base_url: str
    source_type: str
    reliability_weight: int
    is_approved: bool
    check_frequency: str
    rate_limit_rpm: int
    last_crawled_at: Optional[str] = None

class OpportunityCreate(BaseModel):
    organization_name: str
    title: str
    description: str
    opportunity_type: str = "job" # 'job', 'internship', 'hackathon', 'startup'
    experience_level: str = "fresher" # 'fresher', 'no_experience', '0-1_year', '0-2_years', 'other'
    location: Optional[str] = None
    salary_range: Optional[str] = None
    source_url: str
    source_name: Optional[str] = "Official Career Portal"
    source_identifier: Optional[str] = None
    publication_date: Optional[str] = None

class OpportunityOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    title: str
    description: str
    opportunity_type: str
    experience_level: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_url: str
    source_identifier: Optional[str] = None
    status: str
    confidence_score: int = 0
    publication_date: Optional[str] = None
    discovered_at: Optional[str] = None
    contact_count: int = 0
    primary_contact_email: Optional[str] = None
    primary_contact_status: Optional[str] = None

class ContactMethodCreate(BaseModel):
    method_type: str = "email" # 'email', 'phone', 'work_email'
    value: str
    is_primary: bool = True

class ContactCreate(BaseModel):
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: str = "official_channel"
    provenance_notes: Optional[str] = None
    methods: List[ContactMethodCreate] = []

class ContactOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: str
    provenance_notes: Optional[str] = None
    verification_status: str
    confidence_score: int
    is_suppressed: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Enrichment & Verification
# ---------------------------------------------------------------------------

class EnrichmentTriggerRequest(BaseModel):
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    recruiter_name: Optional[str] = None
    company_domain: Optional[str] = None
    provider: str = "contactout" # 'contactout' | 'snovio'
    confirm_credits: bool = Field(..., description="Must explicitly confirm credit usage")

class EnrichmentRequestOut(BaseModel):
    id: str
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    provider: str
    status: str
    credits_estimated: int
    credits_used: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class VerificationTriggerRequest(BaseModel):
    contact_id: Optional[str] = None
    contact_method_id: Optional[str] = None
    email: Optional[str] = None

class VerificationResultOut(BaseModel):
    id: str
    email: str
    status: str # 'deliverable', 'undeliverable', 'catch-all', 'risky', 'unknown', 'verification_failed'
    provider: str
    score: int
    smtp_check: bool
    mx_records: List[str] = []
    checked_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Data Quality Scoring
# ---------------------------------------------------------------------------

class QualityScoreOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    total_score: int # 0-100
    source_reliability_score: int # 0-25
    org_association_score: int # 0-25
    verification_evidence_score: int # 0-20
    data_freshness_score: int # 0-15
    completeness_score: int # 0-15
    score_band: str # 'high_confidence', 'medium_confidence', 'low_confidence', 'suppressed'
    reason_codes: List[str]
    scoring_version: str
    scored_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Campaigns, AI Drafts & Approvals
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    daily_limit: int = 50
    monthly_limit: int = 1000

class CampaignOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    status: str # 'draft', 'active', 'paused', 'completed'
    daily_limit: int
    monthly_limit: int
    sent_count: int
    draft_count: int = 0
    approved_count: int = 0
    created_at: Optional[str] = None

class DraftGenerateRequest(BaseModel):
    campaign_id: str
    opportunity_id: str
    contact_id: str
    tone: Optional[str] = "professional_enthusiastic"
    campaign_objective: Optional[str] = None

class DraftEditRequest(BaseModel):
    subject_line: str
    email_body: str

class CampaignDraftOut(BaseModel):
    id: str
    campaign_id: str
    opportunity_id: str
    contact_id: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    subject_line: str
    email_body: str
    personalization_summary: Optional[str] = None
    claims_used: List[str] = []
    missing_info_warnings: List[str] = []
    confidence_notes: Optional[str] = None
    model_name: str
    prompt_version: str
    status: str # 'generated', 'edited', 'approved', 'rejected'
    created_at: Optional[str] = None

class ApprovalRequest(BaseModel):
    campaign_draft_id: str
    decision: str # 'approved', 'rejected', 'changes_requested'
    review_notes: Optional[str] = None
    approved_recipient: Optional[str] = None
    approved_subject: Optional[str] = None
    approved_body: Optional[str] = None

class ApprovalOut(BaseModel):
    id: str
    campaign_draft_id: str
    reviewed_by_user_id: str
    reviewer_name: Optional[str] = None
    decision: str
    review_notes: Optional[str] = None
    approved_recipient: str
    approved_subject: str
    approved_body: str
    approved_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Email Dispatch & Callbacks
# ---------------------------------------------------------------------------

class DispatchTriggerRequest(BaseModel):
    campaign_draft_id: str
    idempotency_key: Optional[str] = None

class OutreachMessageOut(BaseModel):
    id: str
    campaign_id: str
    campaign_draft_id: str
    recipient_email: str
    subject: str
    idempotency_key: str
    provider: str
    provider_message_id: Optional[str] = None
    send_status: str # 'pending', 'sent', 'failed', 'delivered', 'bounced', 'opened', 'clicked', 'replied'
    error_message: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Suppression Management
# ---------------------------------------------------------------------------

class SuppressionCreate(BaseModel):
    entity_type: str # 'email', 'domain', 'organization'
    value: str
    reason: str # 'user_opt_out', 'hard_bounce', 'complaint', 'manual_block', 'policy'
    notes: Optional[str] = None

class SuppressionOut(BaseModel):
    id: str
    entity_type: str
    value: str
    reason: str
    notes: Optional[str] = None
    suppressed_by_user_id: Optional[str] = None
    created_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Error Center & Automation Jobs
# ---------------------------------------------------------------------------

class AutomationJobOut(BaseModel):
    id: str
    workflow_name: str
    job_type: str
    correlation_id: str
    status: str
    attempts: int
    max_attempts: int
    next_retry_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class AutomationErrorOut(BaseModel):
    id: str
    job_id: Optional[str] = None
    correlation_id: str
    workflow_name: str
    failed_step: str
    failure_category: str # 'network', 'rate_limit', 'validation', 'credential', 'credit_exhaustion', 'source_layout', 'ai_output', 'send_timeout', 'provider_rejection'
    error_message: str
    stack_trace: Optional[str] = None
    is_replay_eligible: bool
    retry_count: int
    recovery_status: str # 'unresolved', 'retrying', 'resolved', 'quarantined'
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None

class ErrorRetryRequest(BaseModel):
    resolution_notes: Optional[str] = None

# ---------------------------------------------------------------------------
# System Health
# ---------------------------------------------------------------------------

class SystemHealthMetrics(BaseModel):
    n8n_status: str
    n8n_uptime_pct: float
    total_leads_discovered: int
    unreviewed_leads: int
    enrichment_queue_size: int
    credits_used_today: int
    credits_monthly_used: int
    credits_monthly_budget: int
    deliverable_emails: int
    active_campaigns: int
    total_emails_sent_today: int
    daily_send_limit: int
    active_errors: int
    quarantined_sources: int
    provider_health: Dict[str, str]
