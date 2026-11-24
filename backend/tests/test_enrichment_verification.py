import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_email_verification_states():
    # Test valid deliverable email
    resp1 = client.post("/api/v1/verification/verify", json={"email": "recruiter@nexusai.io"})
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["status"] == "deliverable"
    assert d1["score"] > 80

    # Test invalid syntax
    resp2 = client.post("/api/v1/verification/verify", json={"email": "invalid-email-format"})
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["status"] == "undeliverable"
    assert d2["score"] == 0

    # Test disposable domain
    resp3 = client.post("/api/v1/verification/verify", json={"email": "tempuser@mailinator.com"})
    assert resp3.status_code == 200
    d3 = resp3.json()
    assert d3["status"] == "undeliverable"

def test_manual_enrichment_credit_confirmation():
    # Attempt enrichment without confirming credits -> Must fail
    resp_fail = client.post("/api/v1/enrichment/enrich", json={
        "provider": "contactout",
        "confirm_credits": False,
        "company_domain": "nexusai.io"
    })
    assert resp_fail.status_code == 400
    assert "Credit confirmation required" in resp_fail.json()["detail"]

    # Attempt enrichment with confirm_credits = True -> Must succeed
    resp_ok = client.post("/api/v1/enrichment/enrich", json={
        "provider": "contactout",
        "confirm_credits": True,
        "company_domain": "nexusai.io",
        "recruiter_name": "Elena Smith"
    })
    assert resp_ok.status_code == 200
    d = resp_ok.json()
    assert d["credits_used"] == 1
    assert d["status"] == "completed"
