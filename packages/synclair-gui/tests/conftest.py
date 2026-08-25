"""
Shared pytest fixtures for synclair-gui backend tests.
"""

import pytest
from fastapi.testclient import TestClient

from synclair_gui.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Log in as the demo user and return an Authorization header dict,
    ready to be spread into any authenticated request.
    """
    response = client.post(
        "/auth/login",
        data={"username": "demo", "password": "synclair-demo"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}