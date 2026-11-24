import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_opportunities():
    resp = client.get("/api/v1/crm/opportunities")
    assert resp.status_code == 200
    opps = resp.json()
    assert isinstance(opps, list)
    assert len(opps) > 0

def test_filter_opportunities_fresher():
    resp = client.get("/api/v1/crm/opportunities?experience_level=fresher")
    assert resp.status_code == 200
    opps = resp.json()
    assert all(o["experience_level"] == "fresher" for o in opps)

def test_duplicate_lead_detection():
    # Ingest lead
    lead_payload = {
        "title": "Graduate Junior Engineer Unique Test",
        "company_name": "TestCorp Robotics",
        "description": "Looking for entry level engineers with zero experience in robotics.",
        "experience_level": "fresher",
        "source_url": "https://careers.testcorp.com/unique-test-job-01",
        "location": "Boston, MA"
    }
    resp1 = client.post("/api/v1/discovery/ingest", json=lead_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "created"

    # Ingest the exact same lead again
    resp2 = client.post("/api/v1/discovery/ingest", json=lead_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "duplicate_skipped"
