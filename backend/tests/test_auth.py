import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.core.security import compute_code_challenge, create_local_demo_token


def test_unauthenticated_request_rejected(client):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    resp = client.get("/api/presentations")
    assert resp.status_code == 401
    assert "Authorization bearer token is missing" in resp.json()["detail"]


def test_demo_login_flow(client):
    """Verify that demo login issues a valid bearer token with expected roles."""
    resp = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["roles"] == ["analyst"]

    # Verify token can access protected endpoints
    token = data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "analyst@atlas-hub.local"


def test_role_enforcement_viewer_denied(client, viewer_token):
    """Verify that viewer role is denied mutation endpoints with 403 Forbidden."""
    resp = client.post(
        "/api/presentations",
        json={
            "title": "Unauthorized Mutation",
            "raw_content": "# Heading\nTest content for unauthorized request.",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403
    assert "Required role 'analyst' not granted" in resp.json()["detail"]


def test_admin_and_analyst_permitted(client, analyst_token):
    """Verify that analyst role is permitted to create presentations."""
    resp = client.post(
        "/api/presentations",
        json={
            "title": "Authorized Creation",
            "raw_content": "# Heading\nValid content for analyst creation.",
        },
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Authorized Creation"


def test_pkce_challenge_computation():
    """Verify standard S256 PKCE code challenge computation."""
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    challenge = compute_code_challenge(verifier)
    assert len(challenge) > 20
    assert "=" not in challenge


def test_demo_mode_refused_in_production():
    """Verify that demo token generation refuses execution when APP_ENV is production."""
    orig_env = settings.APP_ENV
    try:
        settings.APP_ENV = "production"
        with pytest.raises(HTTPException) as exc_info:
            create_local_demo_token()
        assert exc_info.value.status_code == 403
    finally:
        settings.APP_ENV = orig_env


def test_explicit_logout(client, analyst_token):
    """Verify explicit logout endpoint returns confirmation."""
    resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["logged_out"] is True
