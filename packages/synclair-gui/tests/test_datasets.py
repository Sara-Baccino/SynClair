"""
Tests for the datasets router: upload, in-memory registration, and
DataConfig build/validation. All endpoints require authentication.
"""

import io

from fastapi.testclient import TestClient
from tests.test_structure import _upload_and_configure, _wait_for_completion


def _sample_csv_bytes() -> bytes:
    return b"age,city\n25,Milan\n40,Rome\n33,Turin\n"


def test_upload_dataset_returns_preview_and_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(_sample_csv_bytes()), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200

    body = response.json()
    assert body["filename"] == "sample.csv"
    assert body["n_rows"] == 3
    assert body["n_columns"] == 2
    assert {c["name"] for c in body["columns"]} == {"age", "city"}
    assert len(body["preview"]) == 3
    assert body["dataset_id"]


def test_upload_rejects_unsupported_extension(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/datasets/upload",
        files={"file": ("sample.exe", io.BytesIO(b"not a dataset"), "application/octet-stream")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_parse_config_builds_config_for_uploaded_dataset(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    upload_response = client.post(
        "/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(_sample_csv_bytes()), "text/csv")},
        headers=auth_headers,
    )
    dataset_id = upload_response.json()["dataset_id"]

    response = client.post(
        "/datasets/parse-config", json={"dataset_id": dataset_id}, headers=auth_headers
    )
    assert response.status_code == 200

    body = response.json()
    assert body["validation"]["is_valid"] is True

    columns_by_name = {c["name"]: c for c in body["data_config"]["columns"]}
    assert columns_by_name["age"]["numerical"] is True
    assert columns_by_name["city"]["categorical"] is True


def test_parse_config_returns_404_for_unknown_dataset(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/datasets/parse-config", json={"dataset_id": "does-not-exist"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_upload_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(_sample_csv_bytes()), "text/csv")},
    )
    assert response.status_code == 401


def test_parse_config_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/datasets/parse-config", json={"dataset_id": "irrelevant"})
    assert response.status_code == 401


def test_get_dataset_returns_existing_dataset(client: TestClient, auth_headers: dict[str, str]) -> None:
    upload_response = client.post(
        "/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(_sample_csv_bytes()), "text/csv")},
        headers=auth_headers,
    )
    dataset_id = upload_response.json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}", headers=auth_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert body["filename"] == "sample.csv"
    assert body["has_data_config"] is False


def test_get_dataset_reflects_config_presence_after_parse(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    upload_response = client.post(
        "/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(_sample_csv_bytes()), "text/csv")},
        headers=auth_headers,
    )
    dataset_id = upload_response.json()["dataset_id"]
    client.post("/datasets/parse-config", json={"dataset_id": dataset_id}, headers=auth_headers)

    response = client.get(f"/datasets/{dataset_id}", headers=auth_headers)
    assert response.json()["has_data_config"] is True


def test_get_dataset_returns_404_for_unknown_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/datasets/does-not-exist", headers=auth_headers)
    assert response.status_code == 404


def test_get_dataset_requires_authentication(client: TestClient) -> None:
    response = client.get("/datasets/irrelevant")
    assert response.status_code == 401


def test_create_dataset_from_artifact_promotes_clustered_dataset(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    dataset_id = _upload_and_configure(client, auth_headers)

    run_response = client.post(
        "/structure/run",
        json={
            "dataset_id": dataset_id,
            "module_config": {
                "clustering_algorithm": "kmeans",
                "clustering_config": {"n_clusters": 2, "random_state": 42},
            },
        },
        headers=auth_headers,
    )
    job_id = run_response.json()["job_id"]
    _wait_for_completion(client, job_id, auth_headers)

    response = client.post(
        "/datasets/from-artifact",
        json={"source_job_id": job_id, "artifact_name": "clustered_dataset"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["dataset_id"] != dataset_id


def test_create_dataset_from_artifact_with_row_filter(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    dataset_id = _upload_and_configure(client, auth_headers)
    run_response = client.post(
        "/structure/run",
        json={
            "dataset_id": dataset_id,
            "module_config": {
                "clustering_algorithm": "kmeans",
                "clustering_config": {"n_clusters": 2, "random_state": 42},
            },
        },
        headers=auth_headers,
    )
    job_id = run_response.json()["job_id"]
    _wait_for_completion(client, job_id, auth_headers)

    response = client.post(
        "/datasets/from-artifact",
        json={
            "source_job_id": job_id,
            "artifact_name": "clustered_dataset",
            "row_filters": [{"column": "cluster_label", "operator": "in", "value": [0]}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["n_rows"] > 0


def test_create_dataset_from_artifact_unknown_artifact_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    dataset_id = _upload_and_configure(client, auth_headers)
    run_response = client.post(
        "/structure/run",
        json={
            "dataset_id": dataset_id,
            "module_config": {
                "clustering_algorithm": "kmeans",
                "clustering_config": {"n_clusters": 2},
            },
        },
        headers=auth_headers,
    )
    job_id = run_response.json()["job_id"]
    _wait_for_completion(client, job_id, auth_headers)

    response = client.post(
        "/datasets/from-artifact",
        json={"source_job_id": job_id, "artifact_name": "does_not_exist"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_create_dataset_from_artifact_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/datasets/from-artifact", json={"source_job_id": "irrelevant", "artifact_name": "x"}
    )
    assert response.status_code == 401