# API Reference

Base URL: `http://localhost:8000/api/v1`

All protected endpoints require: `Authorization: Bearer <token>`

---

## Authentication

### POST `/auth/login`
Login and receive JWT token.

**Request** (`application/x-www-form-urlencoded`):
```
username=admin@company.com&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "full_name": "Admin User",
    "roles": ["admin"]
  }
}
```

### GET `/auth/me`
Get current user info. Requires auth.

---

## CRM

### GET `/crm/organizations`
List all organizations.

**Query params:** `search`, `limit`, `offset`

### GET `/crm/organizations/{id}`
Get single organization with opportunities.

### GET `/crm/opportunities`
List opportunities with filters.

**Query params:** `search`, `experience_level` (fresher/0_1/0_2/internship/hackathon), `status`, `organization_id`, `limit`, `offset`

### PATCH `/crm/opportunities/{id}`
Update opportunity status or notes.

**Body:** `{ "status": "enriched", "notes": "..." }`

### GET `/crm/contacts`
List contacts with enrichment and verification status.

**Query params:** `search`, `organization_id`, `verification_status`, `limit`

### GET `/crm/contacts/{id}`
Get contact detail with enrichment history.

### GET `/crm/pipeline`
Aggregated pipeline counts by stage.

---

## Lead Discovery

### POST `/discovery/trigger`
Trigger manual lead discovery run.

**Body:** `{ "source_ids": ["uuid1"], "max_results": 50 }`

### GET `/discovery/sources`
List configured approved sources.

---

## Enrichment

### GET `/enrichment/queue`
List contacts needing enrichment.

### POST `/enrichment/contacts/{contact_id}/enrich`
Trigger enrichment for a contact.

**Body:** `{ "provider": "contactout" }` or `"snov_io"`

### GET `/enrichment/contacts/{contact_id}/history`
Get enrichment history for a contact.

---

## Verification

### POST `/verification/verify/{contact_method_id}`
Trigger email verification.

### GET `/verification/status/{contact_method_id}`
Get verification status (deliverable/undeliverable/catch-all/risky/unknown/failed).

---

## Scoring

### POST `/scoring/score/{opportunity_id}`
Run confidence scoring for an opportunity.

**Response:**
```json
{
  "opportunity_id": "uuid",
  "total_score": 82,
  "band": "high",
  "breakdown": {
    "source_reliability": 22,
    "org_contact_association": 20,
    "verification_evidence": 18,
    "data_freshness": 12,
    "completeness": 10
  },
  "reason_codes": ["verified_email", "fresh_data"]
}
```

### GET `/scoring/score/{opportunity_id}`
Get stored score.

---

## Campaigns

### GET `/campaigns`
List all campaigns with draft counts.

### POST `/campaigns`
Create a new campaign.

**Body:**
```json
{
  "name": "SDE Fresher Q1",
  "description": "...",
  "daily_limit": 50,
  "monthly_limit": 1000
}
```

### GET `/campaigns/{id}`
Get campaign detail.

### PATCH `/campaigns/{id}/status`
Update campaign status (draft/active/paused/completed).

### GET `/campaigns/{id}/drafts`
List drafts for a campaign.

### POST `/campaigns/drafts/generate`
Generate AI email draft using Gemini Flash.

**Body:**
```json
{
  "campaign_id": "uuid",
  "opportunity_id": "uuid",
  "contact_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "generated",
  "subject_line": "...",
  "email_body": "...",
  "personalization_summary": "...",
  "claims_used": ["verified job title", "company name from source"],
  "missing_info_warnings": [],
  "confidence_notes": "High confidence — verified email",
  "model_name": "gemini-1.5-flash",
  "prompt_version": "v1.0"
}
```

### PATCH `/campaigns/drafts/{id}`
Edit draft subject and body.

### POST `/campaigns/drafts/{id}/approve`
Human approval of a draft.

**Body:**
```json
{
  "decision": "approved",
  "review_notes": "Looks good",
  "approved_recipient": "hr@company.com",
  "approved_subject": "SDE Role at TechCorp",
  "approved_body": "Dear Hiring Manager, ..."
}
```

### POST `/campaigns/drafts/{id}/reject`
Reject a draft.

### POST `/campaigns/drafts/{id}/dispatch`
Dispatch approved draft (email send). Requires prior approval.

---

## Suppression

### GET `/suppression`
List suppression entries. Query params: `search`, `reason`, `limit`

### POST `/suppression`
Add entry to suppression list.

**Body:**
```json
{
  "value": "user@example.com",
  "suppression_type": "email",
  "reason": "unsubscribed",
  "notes": "Opted out via link"
}
```

### GET `/suppression/check/{email}`
Check if email is suppressed.

**Response:** `{ "suppressed": true, "reason": "unsubscribed" }`

---

## Error Center

### GET `/errors`
List automation errors.

**Query params:** `category`, `recovery_status`, `limit`

### POST `/errors/{job_id}/retry`
Manually retry a failed job.

---

## Health

### GET `/health/status`
Simple health check (unauthenticated).

**Response:** `{ "status": "healthy", "timestamp": "..." }`

### GET `/health/dashboard`
Full system health dashboard (admin only).

**Response:**
```json
{
  "services": {
    "database": "healthy",
    "n8n": "healthy",
    "gemini_api": "healthy",
    "email_provider": "healthy"
  },
  "metrics": {
    "emails_sent_today": 12,
    "pending_approval": 3,
    "unresolved_errors": 0,
    "total_sent": 450
  },
  "queue": {
    "pending_jobs": 2,
    "processing_jobs": 0
  }
}
```

---

## Webhooks

### POST `/webhooks/email-provider`
Receive delivery event callbacks (bounce, delivered, opened).
Verifies HMAC signature. Auto-suppresses hard bounces.

### POST `/webhooks/n8n`
Receive workflow status callbacks from n8n.

---

## Error Responses

All errors follow:
```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Validation error |
| 401 | Missing or invalid JWT |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate, suppressed, already sent) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
