import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.security import hash_password, verify_password, create_access_token

client = TestClient(app)

def test_password_hashing():
    pw = "SuperSecurePassword@2025"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword", h) is False

def test_admin_login():
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@leadintel.org",
        "password": "Admin@123456"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "admin" in data["roles"]

def test_researcher_login():
    resp = client.post("/api/v1/auth/login", json={
        "email": "researcher@leadintel.org",
        "password": "Researcher@123456"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "researcher" in data["roles"]

def test_invalid_login():
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@leadintel.org",
        "password": "WrongPassword123"
    })
    assert resp.status_code == 401
