"""
Tests for the auth router: login with valid/invalid credentials, token
verification via /auth/me, and rejection of missing/invalid tokens.
"""

from fastapi.testclient import TestClient

from synclair_gui.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_login_with_valid_credentials_returns_token() -> None:
    client = _client()
    response = client.post(
        "/auth/login",
        data={"username": "demo", "password": "synclair-demo"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_invalid_password_returns_401() -> None:
    client = _client()
    response = client.post(
        "/auth/login",
        data={"username": "demo", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_with_unknown_username_returns_401() -> None:
    client = _client()
    response = client.post(
        "/auth/login",
        data={"username": "nobody", "password": "irrelevant"},
    )
    assert response.status_code == 401


def test_me_endpoint_with_valid_token_returns_user() -> None:
    client = _client()
    login_response = client.post(
        "/auth/login",
        data={"username": "demo", "password": "synclair-demo"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"username": "demo", "full_name": "SynClair Demo User"}


def test_me_endpoint_without_token_returns_401() -> None:
    client = _client()
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_endpoint_with_garbage_token_returns_401() -> None:
    client = _client()
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401