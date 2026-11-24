-- =============================================================================
-- Migration: 001_initial_schema.sql
-- Automated Lead Generation & Outreach System
-- 21 PostgreSQL Tables with UTC Timestamps, Indexes & Foreign Keys
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 2. ROLES
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE, -- 'admin', 'researcher', 'campaign_manager'
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 3. USER_ROLES
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    PRIMARY KEY (user_id, role_id)
);

-- 4. ORGANIZATIONS
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    size_range VARCHAR(50),
    website_url TEXT,
    linkedin_url TEXT,
    location VARCHAR(255),
    is_suppressed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_org_normalized_name ON organizations(normalized_name);
CREATE INDEX IF NOT EXISTS idx_org_domain ON organizations(domain);
CREATE INDEX IF NOT EXISTS idx_org_suppressed ON organizations(is_suppressed);

-- 5. SOURCES
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'job_board', 'company_careers', 'hackathon_platform', 'recruitment_announcement'
    reliability_weight INTEGER NOT NULL DEFAULT 20 CHECK (reliability_weight BETWEEN 0 AND 25),
    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
    check_frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    rate_limit_rpm INTEGER NOT NULL DEFAULT 30,
    last_crawled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_sources_approved ON sources(is_approved);

-- 6. OPPORTUNITIES
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    opportunity_type VARCHAR(50) NOT NULL, -- 'job', 'internship', 'hackathon', 'startup'
    experience_level VARCHAR(50) NOT NULL, -- 'fresher', 'no_experience', '0-1_year', '0-2_years', 'other'
    location VARCHAR(255),
    salary_range VARCHAR(100),
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_url TEXT NOT NULL,
    source_identifier VARCHAR(255), -- unique remote ID or URL hash
    status VARCHAR(50) NOT NULL DEFAULT 'discovered', -- 'discovered', 'reviewed', 'enrichment_pending', 'ready_for_draft', 'archived'
    confidence_score INTEGER DEFAULT 0 CHECK (confidence_score BETWEEN 0 AND 100),
    publication_date TIMESTAMPTZ,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT uq_opportunity_source_identifier UNIQUE (source_id, source_identifier)
);
CREATE INDEX IF NOT EXISTS idx_opp_org ON opportunities(organization_id);
CREATE INDEX IF NOT EXISTS idx_opp_exp_level ON opportunities(experience_level);
CREATE INDEX IF NOT EXISTS idx_opp_type ON opportunities(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opp_confidence ON opportunities(confidence_score);

-- 7. CONTACTS
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    full_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role_title VARCHAR(255),
    department VARCHAR(100),
    linkedin_url TEXT,
    source VARCHAR(100) NOT NULL DEFAULT 'official_channel', -- 'official_channel', 'contactout', 'snovio', 'manual'
    provenance_notes TEXT,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    confidence_score INTEGER DEFAULT 0 CHECK (confidence_score BETWEEN 0 AND 100),
    is_suppressed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_contact_org ON contacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contact_suppressed ON contacts(is_suppressed);

-- 8. CONTACT_METHODS
CREATE TABLE IF NOT EXISTS contact_methods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    method_type VARCHAR(50) NOT NULL, -- 'email', 'phone', 'work_email'
    value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'unknown', -- 'deliverable', 'undeliverable', 'catch-all', 'risky', 'unknown', 'verification_failed'
    verified_at TIMESTAMPTZ,
    provider_evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT uq_contact_method UNIQUE (contact_id, method_type, value)
);
CREATE INDEX IF NOT EXISTS idx_cm_contact ON contact_methods(contact_id);
CREATE INDEX IF NOT EXISTS idx_cm_value ON contact_methods(value);
CREATE INDEX IF NOT EXISTS idx_cm_status ON contact_methods(verification_status);

-- 9. OPPORTUNITY_CONTACTS
CREATE TABLE IF NOT EXISTS opportunity_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    role_in_opportunity VARCHAR(50) NOT NULL DEFAULT 'recruiter', -- 'recruiter', 'hiring_manager', 'official_channel'
    association_confidence INTEGER DEFAULT 20 CHECK (association_confidence BETWEEN 0 AND 25),
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT uq_opp_contact UNIQUE (opportunity_id, contact_id)
);
CREATE INDEX IF NOT EXISTS idx_opp_contact_opp ON opportunity_contacts(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opp_contact_contact ON opportunity_contacts(contact_id);

-- 10. ENRICHMENT_REQUESTS
CREATE TABLE IF NOT EXISTS enrichment_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL, -- 'contactout', 'snovio'
    requested_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'rejected'
    credits_estimated INTEGER NOT NULL DEFAULT 1,
    credits_used INTEGER NOT NULL DEFAULT 0,
    request_payload JSONB DEFAULT '{}'::jsonb,
    response_payload JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_enrichment_contact ON enrichment_requests(contact_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_status ON enrichment_requests(status);

-- 11. VERIFICATION_RESULTS
CREATE TABLE IF NOT EXISTS verification_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_method_id UUID REFERENCES contact_methods(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'deliverable', 'undeliverable', 'catch-all', 'risky', 'unknown', 'verification_failed'
    provider VARCHAR(50) NOT NULL,
    score INTEGER DEFAULT 0,
    smtp_check BOOLEAN DEFAULT FALSE,
    mx_records JSONB DEFAULT '[]'::jsonb,
    raw_response JSONB DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_vr_email ON verification_results(email);
CREATE INDEX IF NOT EXISTS idx_vr_status ON verification_results(status);

-- 12. DATA_QUALITY_SCORES
CREATE TABLE IF NOT EXISTS data_quality_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'opportunity', 'contact'
    entity_id UUID NOT NULL,
    total_score INTEGER NOT NULL CHECK (total_score BETWEEN 0 AND 100),
    source_reliability_score INTEGER NOT NULL CHECK (source_reliability_score BETWEEN 0 AND 25),
    org_association_score INTEGER NOT NULL CHECK (org_association_score BETWEEN 0 AND 25),
    verification_evidence_score INTEGER NOT NULL CHECK (verification_evidence_score BETWEEN 0 AND 20),
    data_freshness_score INTEGER NOT NULL CHECK (data_freshness_score BETWEEN 0 AND 15),
    completeness_score INTEGER NOT NULL CHECK (completeness_score BETWEEN 0 AND 15),
    score_band VARCHAR(50) NOT NULL, -- 'high_confidence', 'medium_confidence', 'low_confidence', 'suppressed'
    reason_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    scoring_version VARCHAR(20) NOT NULL DEFAULT 'v1.0.0',
    scored_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_dqs_entity ON data_quality_scores(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_dqs_band ON data_quality_scores(score_band);

-- 13. CAMPAIGNS
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    objective TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'paused', 'completed'
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    daily_limit INTEGER NOT NULL DEFAULT 50,
    monthly_limit INTEGER NOT NULL DEFAULT 1000,
    sent_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status);

-- 14. CAMPAIGN_DRAFTS
CREATE TABLE IF NOT EXISTS campaign_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    subject_line TEXT NOT NULL,
    email_body TEXT NOT NULL,
    personalization_summary TEXT,
    claims_used JSONB DEFAULT '[]'::jsonb,
    missing_info_warnings JSONB DEFAULT '[]'::jsonb,
    confidence_notes TEXT,
    model_name VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    input_references JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'generated', -- 'generated', 'edited', 'approved', 'rejected'
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_cd_campaign ON campaign_drafts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_cd_status ON campaign_drafts(status);

-- 15. APPROVALS
CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_draft_id UUID NOT NULL REFERENCES campaign_drafts(id) ON DELETE CASCADE,
    reviewed_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    decision VARCHAR(50) NOT NULL, -- 'approved', 'rejected', 'changes_requested'
    review_notes TEXT,
    approved_recipient VARCHAR(255) NOT NULL,
    approved_subject TEXT NOT NULL,
    approved_body TEXT NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_approvals_draft ON approvals(campaign_draft_id);
CREATE INDEX IF NOT EXISTS idx_approvals_decision ON approvals(decision);

-- 16. OUTREACH_MESSAGES
CREATE TABLE IF NOT EXISTS outreach_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    campaign_draft_id UUID NOT NULL REFERENCES campaign_drafts(id) ON DELETE RESTRICT,
    approval_id UUID NOT NULL REFERENCES approvals(id) ON DELETE RESTRICT,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL DEFAULT 'mock',
    provider_message_id VARCHAR(255),
    send_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'delivered', 'bounced', 'opened', 'clicked', 'replied'
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_om_campaign ON outreach_messages(campaign_id);
CREATE INDEX IF NOT EXISTS idx_om_recipient ON outreach_messages(recipient_email);
CREATE INDEX IF NOT EXISTS idx_om_status ON outreach_messages(send_status);
CREATE INDEX IF NOT EXISTS idx_om_idempotency ON outreach_messages(idempotency_key);

-- 17. MESSAGE_EVENTS
CREATE TABLE IF NOT EXISTS message_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outreach_message_id UUID NOT NULL REFERENCES outreach_messages(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'delivered', 'open', 'click', 'bounce', 'reply', 'unsubscribe'
    provider VARCHAR(50) NOT NULL,
    provider_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_timestamp TIMESTAMPTZ NOT NULL,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_me_msg ON message_events(outreach_message_id);
CREATE INDEX IF NOT EXISTS idx_me_event_type ON message_events(event_type);

-- 18. SUPPRESSION_ENTRIES
CREATE TABLE IF NOT EXISTS suppression_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'email', 'domain', 'organization'
    value VARCHAR(255) NOT NULL UNIQUE,
    reason VARCHAR(50) NOT NULL, -- 'user_opt_out', 'hard_bounce', 'complaint', 'manual_block', 'policy'
    notes TEXT,
    suppressed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_suppression_val ON suppression_entries(value);
CREATE INDEX IF NOT EXISTS idx_suppression_type ON suppression_entries(entity_type);

-- 19. AUTOMATION_JOBS
CREATE TABLE IF NOT EXISTS automation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    correlation_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'retrying'
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_payload JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_jobs_workflow ON automation_jobs(workflow_name);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON automation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_correlation ON automation_jobs(correlation_id);

-- 20. AUTOMATION_ERRORS
CREATE TABLE IF NOT EXISTS automation_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES automation_jobs(id) ON DELETE SET NULL,
    correlation_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(100) NOT NULL,
    failed_step VARCHAR(100) NOT NULL,
    failure_category VARCHAR(50) NOT NULL, -- 'network', 'rate_limit', 'validation', 'credential', 'credit_exhaustion', 'source_layout', 'ai_output', 'send_timeout', 'provider_rejection'
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    is_replay_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    recovery_status VARCHAR(50) NOT NULL DEFAULT 'unresolved', -- 'unresolved', 'retrying', 'resolved', 'quarantined'
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_ae_correlation ON automation_errors(correlation_id);
CREATE INDEX IF NOT EXISTS idx_ae_category ON automation_errors(failure_category);
CREATE INDEX IF NOT EXISTS idx_ae_status ON automation_errors(recovery_status);

-- 21. AUDIT_LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
