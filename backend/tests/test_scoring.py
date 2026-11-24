import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_confidence_scoring_factors():
    # 1. Fetch an opportunity
    opps = client.get("/api/v1/crm/opportunities").json()
    assert len(opps) > 0
    opp_id = opps[0]["id"]

    # 2. Evaluate score
    resp = client.post(f"/api/v1/scoring/evaluate/{opp_id}")
    assert resp.status_code == 200
    score = resp.json()

    # Check 5 exact factors
    assert 0 <= score["source_reliability_score"] <= 25
    assert 0 <= score["org_association_score"] <= 25
    assert 0 <= score["verification_evidence_score"] <= 20
    assert 0 <= score["data_freshness_score"] <= 15
    assert 0 <= score["completeness_score"] <= 15

    total = (
        score["source_reliability_score"] +
        score["org_association_score"] +
        score["verification_evidence_score"] +
        score["data_freshness_score"] +
        score["completeness_score"]
    )
    assert score["total_score"] == total
    assert 0 <= score["total_score"] <= 100

    # Check score bands
    if score["total_score"] >= 80:
        assert score["score_band"] == "high_confidence"
    elif score["total_score"] >= 60:
        assert score["score_band"] == "medium_confidence"
    else:
        assert score["score_band"] in ["low_confidence", "suppressed"]

    assert isinstance(score["reason_codes"], list)
    assert len(score["reason_codes"]) > 0
