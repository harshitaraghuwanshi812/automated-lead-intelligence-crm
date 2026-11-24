import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_provider_callback_bounce_auto_suppression():
    bounce_email = "bounced-applicant@fakemail.org"
    
    # Send provider callback indicating a hard bounce
    resp = client.post("/api/v1/webhooks/provider", json={
        "event_id": "evt_bounce_test_12345",
        "event_type": "bounce",
        "recipient_email": bounce_email,
        "provider_message_id": "msg_sample_987"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"

    # Verify that email was auto-suppressed
    chk = client.get(f"/api/v1/suppressions/check/{bounce_email}").json()
    assert chk["is_suppressed"] is True

def test_webhook_event_idempotency():
    # Sending the same event_id twice must be ignored
    payload = {
        "event_id": "evt_idempotency_unique_001",
        "event_type": "open",
        "recipient_email": "test@domain.com"
    }
    r1 = client.post("/api/v1/webhooks/provider", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed"

    r2 = client.post("/api/v1/webhooks/provider", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate_event_ignored"

def test_error_center_retry():
    errors = client.get("/api/v1/errors").json()
    assert len(errors) > 0
    err = errors[0]
    err_id = err["id"]

    retry_resp = client.post(f"/api/v1/errors/{err_id}/retry", json={
        "resolution_notes": "Retrying after checking network route."
    })
    assert retry_resp.status_code == 200
    data = retry_resp.json()
    assert data["status"] == "retry_scheduled"
    assert "next_retry_at" in data
