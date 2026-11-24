<div align="center">

# 🚀 Automated Lead Generation & Outreach System

### AI-Powered Lead Intelligence · CRM · Campaign Automation

[![CI](https://github.com/YOUR_USERNAME/lead-intelligence-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/lead-intelligence-crm/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-12%2F12%20Passing-brightgreen?style=flat-square&logo=pytest)](backend/run_tests.py)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-06B6D4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](docker/docker-compose.yml)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**A production-grade system for automated lead discovery, AI-powered email drafting, and human-approved campaign dispatch.**  
Built from an 18-page technical specification — no shortcuts, no ORMs, all real engineering.

[Features](#-features) · [Architecture](#-architecture) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [API Docs](#-api-reference) · [Deploy](#-deployment)

</div>

---

## 🎯 What This Does

Most "outreach tools" are just form-fillers. This system is a full pipeline:

```
Approved Sources → Lead Discovery → Deduplication → Enrichment → Verification
     → AI Email Draft (Gemini Flash) → Human Review & Approval → Campaign Dispatch
                                              ↑
                               Zero automated sends without human approval
```

Every step has safety controls:
- **No LinkedIn scraping** — only approved, open data sources
- **Email requires human approval** — the dispatch gate checks 7 conditions before any send
- **AI never invents facts** — Gemini Flash receives only verified data from your database
- **Idempotency** — duplicate send prevention on every dispatch
- **Suppression enforced** — opt-outs and bounces block future sends automatically

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📊 CRM Dashboard
- Organizations, Contacts, Opportunities
- Lead pipeline — Table + Kanban views
- Experience-level filters (Fresher / 0–1y / 0–2y / Internship / Hackathon)
- Search, sort, filter across all entities
- Source provenance tracking

### 🧠 AI Email Drafting
- Gemini Flash-powered personalization
- Zero-hallucination guarantees — only verified facts
- Subject line + full body generation
- Personalization summary + claims used
- Missing info warnings
- Versioned prompts stored with every draft

</td>
<td width="50%">

### 🎯 Confidence Scoring
| Factor | Points |
|--------|--------|
| Source Reliability | 25 |
| Org & Contact Association | 25 |
| Verification Evidence | 20 |
| Data Freshness | 15 |
| Completeness | 15 |
| **Total** | **100** |

Bands: **High** (80–100) · **Medium** (60–79) · **Low** (<60) · **Suppressed**

### 🔒 Human Approval Gate
7 mandatory pre-send checks:
1. Draft approved by a human reviewer
2. Recipient email verified
3. Not in suppression list
4. Not a duplicate send (idempotency key)
5. Daily send limit not exceeded
6. Monthly send limit not exceeded
7. Campaign is in active state

</td>
</tr>
</table>

<details>
<summary><b>See all 11 modules →</b></summary>

| Module | Description |
|--------|-------------|
| **Auth & RBAC** | JWT auth · 4 roles: Admin, Researcher, Campaign Manager, Viewer |
| **Lead Discovery** | Daily n8n workflow · Approved sources · Deduplication via URL hash |
| **CRM** | Organizations, Contacts, Opportunities with full CRUD |
| **Contact Enrichment** | ContactOut + Snov.io · Credit confirmation modal · History tracking |
| **Email Verification** | 6-state engine: deliverable, undeliverable, catch-all, risky, unknown, failed |
| **Confidence Scoring** | 5-factor 100-point system · Explainable reason codes |
| **Gemini AI Drafts** | Personalized emails · Zero hallucination · Stored input refs |
| **Campaign Manager** | Create → Generate → Review/Edit → Approve → Dispatch |
| **Email Dispatch** | 7-check safety gate · Idempotency · Daily/monthly limits |
| **Error Center** | Correlation IDs · Retry with exponential backoff + jitter |
| **System Health** | Service status · API usage · Credit tracking · Auto-refresh |

</details>

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Cloudflare (DNS + CDN)                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
┌─────▼──────┐              ┌───────▼────────┐
│   React    │              │    FastAPI     │
│  Frontend  │◄────API─────►│    Backend     │
│ (Vite +    │              │ (Python 3.11+) │
│ Tailwind)  │              │                │
│ Cloudflare │              │  11 routers    │
│   Pages    │              │  8 services    │
└────────────┘              │  3 repos       │
                            └───────┬────────┘
                                    │ psycopg3
                            ┌───────▼────────┐
                            │ Neon PostgreSQL │
                            │  (21 tables)   │
                            └───────┬────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                 │
           ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
           │ n8n Community│  │  Playwright  │  │Gemini Flash │
           │  (9 workflows│  │   Worker     │  │    API      │
           │   + webhooks)│  │(Approved srcs│  │             │
           └──────────────┘  └─────────────┘  └─────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | React 18 + Vite + Tailwind CSS v4 | Fast builds, modern DX, Cloudflare Pages compatible |
| **Backend** | Python + FastAPI + psycopg3 | Async-ready, type-safe, direct SQL (no ORM bloat) |
| **Database** | Neon PostgreSQL | Serverless Postgres, free tier, `?sslmode=require` |
| **Automation** | n8n Community Edition | 9 visual workflows, self-hosted, webhook-driven |
| **AI** | Google Gemini Flash API | Fast, cheap, multimodal — with hallucination guardrails |
| **Infra** | Docker Compose + Caddy | One-command deploy, automatic HTTPS |
| **Hosting** | Oracle Cloud Free VM | 4 OCPUs / 24 GB RAM — permanently free |
| **CDN** | Cloudflare Pages + DNS | Global edge, free, `_redirects` for SPA routing |

---

## 📁 Project Structure

```
lead-intelligence-crm/
├── 📂 backend/
│   ├── app/
│   │   ├── auth/           # JWT + bcrypt + RBAC
│   │   ├── models/         # Pydantic v2 schemas (no EmailStr dep)
│   │   ├── repositories/   # CRM, Campaign, Error — direct SQL
│   │   ├── routers/        # 11 route modules (auth, crm, campaign...)
│   │   └── services/       # Scoring, Gemini, Dispatch, Verification...
│   ├── migrations/
│   │   ├── 001_initial_schema.sql  # 21 tables + FK + indexes
│   │   └── seed_data.py            # Realistic demo data
│   ├── tests/              # 6 test files, 12 test cases
│   └── run_tests.py        # Sync test runner (12/12 passing)
│
├── 📂 frontend/
│   ├── src/
│   │   ├── api/            # Axios client + typed API calls
│   │   ├── components/     # Layout, UI primitives, badges
│   │   ├── contexts/       # AuthContext (JWT + RBAC)
│   │   └── pages/          # 11 page views
│   └── public/_redirects   # Cloudflare Pages SPA routing
│
├── 📂 n8n/workflows/       # 9 importable workflow JSON files
├── 📂 worker/              # Playwright approved-source scraper
├── 📂 docker/              # docker-compose.yml + Caddyfile
├── 📂 .github/workflows/   # CI (test + build) + CD (Cloudflare deploy)
└── 📄 .env.example
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Clone & configure
```bash
git clone https://github.com/YOUR_USERNAME/lead-intelligence-crm.git
cd lead-intelligence-crm
cp .env.example .env
# Add your API keys to .env (see Environment Variables section in README)
```

### 2. Backend (runs with zero external dependencies)
```bash
cd backend
pip install -r requirements.txt

# Run all 12 tests
python run_tests.py

# Start API server
python -m uvicorn app.main:app --reload --port 8000
# → Swagger UI: http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# → Open: http://localhost:5173
```

### 4. Login
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@company.com` | `admin123` |
| Researcher | `researcher@company.com` | `researcher123` |
| Campaign Manager | `campaign@company.com` | `campaign123` |

### 5. Full stack with Docker
```bash
cd docker
docker compose up -d
# → Frontend: https://your-domain.com
# → API docs: https://your-domain.com/api/v1/docs
# → n8n:      https://n8n.your-domain.com
```

---

## 🧪 Tests

```bash
cd backend
python run_tests.py
```

```
=====================================================================
RUNNING AUTOMATED LEAD GENERATION & OUTREACH SYSTEM TEST SUITE
=====================================================================
  [PASS] Database schema & 21-table seeding integrity
  [PASS] Password hashing and bcrypt verification
  [PASS] JWT Token generation & RBAC roles for Admin, Researcher, Campaign Manager
  [PASS] Opportunity filtering (fresher, 0-1y, 0-2y, internships, hackathons)
  [PASS] Deduplication prevention via source URL hash & title normalization
  [PASS] Manual enrichment credit confirmation & tracking (ContactOut / Snov.io)
  [PASS] Multi-state verification (deliverable, undeliverable, risky, catch-all)
  [PASS] Exact 5-factor confidence scoring & explainable reason codes
  [PASS] Structured Gemini Flash email draft with verified facts & versioned prompt
  [PASS] Mandatory human approval, pre-send checks & idempotency duplicate prevention
  [PASS] Suppression list, bounce auto-suppression & callback event idempotency
  [PASS] Error Center failure categorization, jitter backoff & system health metrics

TEST RESULTS: 12 PASSED, 0 FAILED
```

---

## 🔑 Environment Variables

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# JWT Authentication
JWT_SECRET_KEY=your-32-character-minimum-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# Contact Enrichment (optional — works without these)
CONTACTOUT_API_KEY=
SNOVIO_USER_ID=
SNOVIO_API_KEY=

# Email Provider (SendGrid recommended)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=outreach@yourdomain.com
FROM_NAME=Your Name

# n8n Integration
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_SECRET=your-n8n-webhook-secret

# Webhook Security
PROVIDER_WEBHOOK_SECRET=your-email-provider-webhook-secret
```

---

## 🌐 n8n Workflows

Import all 9 JSON files from `n8n/workflows/` into your n8n instance:

| # | Workflow | Trigger | Purpose |
|---|----------|---------|---------|
| 01 | Daily Lead Discovery | Cron 06:00 UTC | Crawl approved sources for new opportunities |
| 02 | Source Processing | Webhook | Normalize, deduplicate, store raw leads |
| 03 | Manual Enrichment | Webhook | Trigger ContactOut/Snov.io per contact |
| 04 | Email Verification | Webhook | Run 6-state email verification |
| 05 | AI Draft Generation | Webhook | Gemini Flash email draft creation |
| 06 | Campaign Dispatch | Webhook | Approved email send with 7-check gate |
| 07 | Follow-Up Evaluation | Cron | Evaluate threads for follow-up eligibility |
| 08 | Provider Callbacks | Webhook | Process bounce/open/click events |
| 09 | Error Workflow | Webhook | Catch-all error handler with retry |

---

## 📡 API Reference

Full docs auto-generated at `http://localhost:8000/docs` (Swagger UI).

Quick reference:

```
POST   /api/v1/auth/login                    # Get JWT token
GET    /api/v1/crm/opportunities             # List opportunities with filters
GET    /api/v1/crm/pipeline                  # Pipeline counts by stage
POST   /api/v1/scoring/score/{id}            # Run confidence scoring
POST   /api/v1/enrichment/contacts/{id}/enrich  # Trigger enrichment
POST   /api/v1/campaigns/drafts/generate     # Generate AI email draft
POST   /api/v1/campaigns/drafts/{id}/approve # Human approval
POST   /api/v1/campaigns/drafts/{id}/dispatch # Send approved email
GET    /api/v1/suppression/check/{email}     # Check suppression status
GET    /api/v1/health/dashboard              # Full system health
```

See [API.md](API.md) for complete documentation with request/response examples.

---

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions:

1. **Oracle Cloud Free VM** — ARM64, 4 OCPUs / 24 GB RAM
2. **Neon PostgreSQL** — Free serverless Postgres, run migrations
3. **Docker Compose** — `docker compose up -d` deploys everything
4. **Caddy** — Automatic HTTPS, reverse proxy to FastAPI + n8n
5. **Cloudflare Pages** — React frontend via GitHub Actions CD
6. **Cloudflare DNS** — Proxied A records for API + n8n subdomains

---

## 🛡 Compliance & Ethics

This system is built with hard-coded safety rules that **cannot be bypassed**:

| ❌ Prohibited | ✅ Enforced |
|--------------|------------|
| LinkedIn scraping or automation | Only approved open data sources |
| CAPTCHA bypassing | Playwright respects all bot signals |
| Sending without approval | 7-step human approval gate |
| Emailing suppressed contacts | Suppression checked before every send |
| AI-invented facts | Gemini receives only verified DB records |
| Hardcoded secrets | All credentials in environment variables |

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and deploy.

---

<div align="center">

**Built with ❤️ using FastAPI · React · PostgreSQL · Gemini · n8n**

⭐ Star this repo if you found it useful!

</div>
