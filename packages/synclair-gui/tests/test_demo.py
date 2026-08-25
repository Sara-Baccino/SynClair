"""
Tests for the public demo router: unauthenticated access, real
StructureModule execution against fixed synthetic datasets, input
validation, and non-interference with dataset_store/job_manager.
"""

from fastapi.testclient import TestClient

from synclair_gui.services.dataset_store import dataset_store
from synclair_gui.services.job_manager import job_manager


def test_list_demo_tools_requires_no_auth(client: TestClient) -> None:
    response = client.get("/demo/tools")
    assert response.status_code == 200

    body = response.json()
    assert any(tool["id"] == "structure" for tool in body["tools"])
    dataset_names = {d["name"] for d in body["demo_datasets"]}
    assert dataset_names == {"blobs_2d", "elongated_clusters", "clinical_like"}


def test_run_demo_structure_requires_no_auth_and_returns_clusters(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "blobs_2d", "n_clusters": 3, "include_projection": True},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["dataset_name"] == "blobs_2d"
    assert body["n_observations"] == 60  # 3 clusters * 20 points
    assert body["n_features"] == 2
    assert len(body["labels"]) == body["n_observations"]
    assert body["metrics"]["n_clusters"] == 3
    assert "silhouette" in body["metrics"]
    assert body["embedding"] is not None
    assert len(body["embedding"]) == body["n_observations"]


def test_run_demo_structure_without_projection_omits_embedding(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "clinical_like", "n_clusters": 2, "include_projection": False},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["embedding"] is None


def test_run_demo_structure_rejects_unknown_dataset_name(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "not-a-real-dataset"},
    )
    # Rejected at the schema level (Literal), before reaching the handler.
    assert response.status_code == 422


def test_run_demo_structure_rejects_out_of_range_n_clusters(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "blobs_2d", "n_clusters": 100},
    )
    assert response.status_code == 422


def test_demo_endpoints_do_not_require_authorization_header(client: TestClient) -> None:
    # Explicitly no Authorization header anywhere in this test module;
    # this test just documents/asserts the intent for both endpoints.
    tools_response = client.get("/demo/tools")
    run_response = client.post("/demo/structure/run", json={"dataset_name": "blobs_2d"})
    assert tools_response.status_code == 200
    assert run_response.status_code == 200


def test_demo_run_does_not_touch_dataset_store_or_job_manager(client: TestClient) -> None:
    datasets_before = dict(dataset_store._records)
    jobs_before = dict(job_manager._jobs)

    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "elongated_clusters", "n_clusters": 2},
    )
    assert response.status_code == 200

    assert dataset_store._records == datasets_before
    assert job_manager._jobs == jobs_before