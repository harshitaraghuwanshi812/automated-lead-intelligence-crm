import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_campaign_draft_generation_and_approval():
    # 1. Fetch campaigns, opportunities, and contacts
    camps = client.get("/api/v1/campaigns").json()
    assert len(camps) > 0
    camp_id = camps[0]["id"]

    opps = client.get("/api/v1/crm/opportunities").json()
    assert len(opps) > 0
    opp_id = opps[0]["id"]

    contacts = client.get("/api/v1/crm/contacts").json()
    assert len(contacts) > 0
    contact_id = contacts[0]["id"]

    # 2. Generate Gemini Flash AI Draft
    gen_resp = client.post("/api/v1/campaigns/drafts/generate", json={
        "campaign_id": camp_id,
        "opportunity_id": opp_id,
        "contact_id": contact_id
    })
    assert gen_resp.status_code == 200
    draft = gen_resp.json()
    assert "subject_line" in draft
    assert "email_body" in draft
    assert draft["status"] == "generated"
    assert "claims_used" in draft
    draft_id = draft["id"]

    # 3. Attempt dispatch WITHOUT approval -> MUST BE BLOCKED
    disp_blocked = client.post(f"/api/v1/campaigns/drafts/{draft_id}/dispatch", json={})
    assert disp_blocked.status_code == 403
    assert "mandatory human approval" in disp_blocked.json()["detail"]

    # 4. Edit draft
    edit_resp = client.put(f"/api/v1/campaigns/drafts/{draft_id}", json={
        "subject_line": "Updated Subject Line by Campaign Manager",
        "email_body": "Updated Body reviewed by human manager."
    })
    assert edit_resp.status_code == 200
    assert edit_resp.json()["subject_line"] == "Updated Subject Line by Campaign Manager"

    # 5. Provide Human Approval
    appr_resp = client.post(f"/api/v1/campaigns/drafts/{draft_id}/approve", json={
        "campaign_draft_id": draft_id,
        "decision": "approved",
        "review_notes": "Reviewed and approved for dispatch."
    })
    assert appr_resp.status_code == 200
    assert appr_resp.json()["decision"] == "approved"

    # 6. Dispatch with Human Approval -> MUST SUCCEED
    disp_ok = client.post(f"/api/v1/campaigns/drafts/{draft_id}/dispatch", json={})
    assert disp_ok.status_code == 200
    assert disp_ok.json()["status"] == "dispatched"

    # 7. Attempt duplicate dispatch with same idempotency key -> Duplicate Prevention
    disp_dup = client.post(f"/api/v1/campaigns/drafts/{draft_id}/dispatch", json={})
    assert disp_dup.status_code == 200
    assert disp_dup.json()["status"] == "duplicate_prevented"

def test_suppression_blocks_dispatch():
    # Add an email to suppression list
    supp_email = "suppressed-target@company.com"
    client.post("/api/v1/suppressions", json={
        "entity_type": "email",
        "value": supp_email,
        "reason": "user_opt_out"
    })

    # Verify check endpoint
    chk = client.get(f"/api/v1/suppressions/check/{supp_email}").json()
    assert chk["is_suppressed"] is True
