# n8n Automation Workflows

This directory contains the complete set of 9 self-hosted n8n workflow JSON definitions for the **Automated Lead Generation & Outreach System** as specified in PRD Section 8 & Section 10.

## Workflow Overview

| File | Trigger | Purpose |
| :--- | :--- | :--- |
| `01_daily_lead_discovery.json` | Schedule (`0 6 * * *`) | Triggers daily Playwright crawler for approved sources. |
| `02_source_processing.json` | Webhook / Internal event | Normalizes and classifies opportunities (fresher, 0-1y, 0-2y, internships). |
| `03_manual_enrichment.json` | Dashboard action | Verifies researcher credit confirmation and calls ContactOut / Snov.io APIs. |
| `04_email_verification.json` | Webhook / User action | Runs multi-tier deliverability check and updates confidence scores. |
| `05_ai_draft_generation.json` | Backend event | Invokes Google Gemini Flash AI model with structured prompt and strict facts. |
| `06_campaign_dispatch.json` | Manual approval / Webhook | Verifies human approval, suppression, idempotency, and dispatches email. |
| `07_follow_up_evaluation.json` | Schedule (`0 14 * * *`) | Evaluates reply, bounce, and opt-out cancellation rules for follow-up steps. |
| `08_provider_callback_processing.json` | Webhook | Receives delivery, open, click, bounce, and unsubscribe provider events. |
| `09_error_workflow.json` | Error trigger | Categorizes failures (network, rate limits, schema) and logs to Error Center. |

## How to Import into n8n

1. Start your Docker Compose stack (`docker compose up -d`).
2. Open your n8n UI at `https://your-domain.com/n8n/` (or `http://localhost:5678`).
3. Click on **Workflows** -> **Import from File**.
4. Select the JSON files from `n8n/workflows/`.
5. Activate the workflows.
