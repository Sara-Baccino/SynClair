"""
Tests for the FastAPI app factory: verifies the app builds, CORS is
configured, and every domain router is mounted and reachable at its
real, current endpoints (not the Step 1 placeholder /ping stubs, which
no longer exist now that auth/datasets/structure expose their actual
functionality).
"""

from fastapi.testclient import TestClient

from synclair_gui.app import create_app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_router_is_mounted() -> None:
    client = TestClient(create_app())
    # /auth/login exists and responds (401 for missing form data is fine;
    # what matters here is that it's not a 404, i.e. the router is mounted).
    response = client.post("/auth/login", data={})
    assert response.status_code != 404


def test_datasets_router_is_mounted() -> None:
    client = TestClient(create_app())
    response = client.post("/datasets/parse-config", json={"dataset_id": "x"})
    # 401 (unauthenticated) proves the route exists and auth is wired in;
    # a 404 here would mean the router isn't mounted at all.
    assert response.status_code != 404


def test_structure_router_is_mounted() -> None:
    client = TestClient(create_app())
    response = client.get("/structure/jobs/does-not-exist")
    assert response.status_code != 404 or response.json()["detail"] != "Not Found"


def test_demo_router_is_mounted() -> None:
    client = TestClient(create_app())
    response = client.get("/demo/tools")
    assert response.status_code == 200


def test_cors_headers_present_for_allowed_origin() -> None:
    client = TestClient(create_app())
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"