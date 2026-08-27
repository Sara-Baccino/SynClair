"""
Tests for the public demo router: unauthenticated access, real
StructureModule execution against Iris/Wine, inline-dataset chaining,
input validation, and non-interference with dataset_store/job_manager.
"""

from fastapi.testclient import TestClient

from synclair_gui.services.dataset_store import dataset_store
from synclair_gui.services.job_manager import job_manager


def test_list_demo_tools_requires_no_auth(client: TestClient) -> None:
    response = client.get("/demo/tools")
    assert response.status_code == 200

    body = response.json()
    dataset_names = {d["name"] for d in body["demo_datasets"]}
    assert dataset_names == {"iris", "wine"}
    iris = next(d for d in body["demo_datasets"] if d["name"] == "iris")
    assert iris["n_rows"] == 150
    assert iris["n_numerical"] == 4
    assert iris["n_categorical"] == 1


def test_run_demo_structure_on_named_dataset(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "iris", "n_clusters": 3, "include_projection": True},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["n_observations"] == 150
    assert len(body["labels"]) == 150
    assert body["embedding"] is not None
    assert len(body["clustered_rows"]) == 150


def test_run_demo_structure_on_inline_dataset(client: TestClient) -> None:
    first_response = client.post(
        "/demo/structure/run", json={"dataset_name": "wine", "n_clusters": 3}
    )
    clustered_rows = first_response.json()["clustered_rows"]
    columns = list(clustered_rows[0].keys())

    second_response = client.post(
        "/demo/structure/run",
        json={
            "inline_dataset": {"columns": columns, "rows": clustered_rows},
            "n_clusters": 2,
            "include_projection": False,
        },
    )
    assert second_response.status_code == 200
    body = second_response.json()
    assert body["success"] is True
    assert body["n_observations"] == len(clustered_rows)
    assert body["dataset_label"] == "Previous analysis output"


def test_run_demo_structure_rejects_both_sources(client: TestClient) -> None:
    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "iris", "inline_dataset": {"columns": ["a"], "rows": [{"a": 1}]}},
    )
    assert response.status_code == 422


def test_run_demo_structure_rejects_neither_source(client: TestClient) -> None:
    response = client.post("/demo/structure/run", json={})
    assert response.status_code == 422


def test_run_demo_structure_rejects_unknown_dataset_name(client: TestClient) -> None:
    response = client.post("/demo/structure/run", json={"dataset_name": "not-real"})
    assert response.status_code == 422


def test_demo_run_does_not_touch_dataset_store_or_job_manager(client: TestClient) -> None:
    datasets_before = dict(dataset_store._records)
    jobs_before = dict(job_manager._jobs)

    response = client.post("/demo/structure/run", json={"dataset_name": "wine", "n_clusters": 2})
    assert response.status_code == 200

    assert dataset_store._records == datasets_before
    assert job_manager._jobs == jobs_before

def test_run_demo_structure_excludes_column(client: TestClient) -> None:
    tools_response = client.get("/demo/tools")
    iris_columns = next(d for d in tools_response.json()["demo_datasets"] if d["name"] == "iris")["columns"]
    excluded = [c["name"] for c in iris_columns if c["categorical"]]

    response = client.post(
        "/demo/structure/run",
        json={"dataset_name": "iris", "n_clusters": 3, "excluded_columns": excluded},
    )
    assert response.status_code == 200
    body = response.json()
    assert "species" not in body["feature_names"]