"""
End-to-end test of the structure router: upload -> parse-config -> run
-> poll -> result, using a small deterministic synthetic dataset. All
endpoints require authentication.
"""

import io
import time

from fastapi.testclient import TestClient


def _synthetic_csv_bytes() -> bytes:
    rows = ["x,y"]
    for i in range(10):
        rows.append(f"{i * 0.1},{i * 0.1}")
    for i in range(10):
        rows.append(f"{10 + i * 0.1},{10 + i * 0.1}")
    return ("\n".join(rows) + "\n").encode("utf-8")


def _upload_and_configure(client: TestClient, auth_headers: dict[str, str]) -> str:
    upload_response = client.post(
        "/datasets/upload",
        files={"file": ("points.csv", io.BytesIO(_synthetic_csv_bytes()), "text/csv")},
        headers=auth_headers,
    )
    dataset_id = upload_response.json()["dataset_id"]

    config_response = client.post(
        "/datasets/parse-config", json={"dataset_id": dataset_id}, headers=auth_headers
    )
    assert config_response.json()["validation"]["is_valid"] is True

    return dataset_id


def _wait_for_completion(
    client: TestClient, job_id: str, auth_headers: dict[str, str], timeout_seconds: float = 10.0
) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        status_response = client.get(f"/structure/jobs/{job_id}", headers=auth_headers)
        body = status_response.json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.1)
    raise TimeoutError(f"Job '{job_id}' did not finish within {timeout_seconds}s")


def test_full_structure_run_produces_clusters_and_metrics(
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
    assert run_response.status_code == 202
    job_id = run_response.json()["job_id"]

    final_status = _wait_for_completion(client, job_id, auth_headers)
    assert final_status["status"] == "completed"

    result_response = client.get(f"/structure/jobs/{job_id}/result", headers=auth_headers)
    assert result_response.status_code == 200

    body = result_response.json()
    assert body["success"] is True
    assert body["metrics"]["n_clusters"] == 2
    assert "silhouette" in body["metrics"]

    dataset_names = {d["name"] for d in body["datasets"]}
    assert "clustered_dataset" in dataset_names


def test_run_returns_422_for_invalid_module_config(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    dataset_id = _upload_and_configure(client, auth_headers)

    response = client.post(
        "/structure/run",
        json={
            "dataset_id": dataset_id,
            "module_config": {
                "clustering_algorithm": "kmeans",
                "clustering_config": {"min_cluster_size": 15},  # mismatched config type
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_run_returns_404_for_unknown_dataset(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/structure/run",
        json={
            "dataset_id": "does-not-exist",
            "module_config": {"clustering_algorithm": "kmeans", "clustering_config": {}},
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_result_returns_409_before_completion(client: TestClient, auth_headers: dict[str, str]) -> None:
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

    status_response = client.get(f"/structure/jobs/{job_id}", headers=auth_headers)
    if status_response.json()["status"] not in ("completed", "failed"):
        result_response = client.get(f"/structure/jobs/{job_id}/result", headers=auth_headers)
        assert result_response.status_code == 409

    _wait_for_completion(client, job_id, auth_headers)


def test_run_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/structure/run",
        json={
            "dataset_id": "irrelevant",
            "module_config": {"clustering_algorithm": "kmeans", "clustering_config": {}},
        },
    )
    assert response.status_code == 401


def test_job_status_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/structure/jobs/irrelevant")
    assert response.status_code == 401

def test_download_table_returns_csv_content(client: TestClient, auth_headers: dict[str, str]) -> None:
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

    response = client.get(
        f"/structure/jobs/{job_id}/download/datasets/clustered_dataset", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "cluster_label" in response.text.splitlines()[0]


def test_download_unknown_table_name_returns_404(client: TestClient, auth_headers: dict[str, str]) -> None:
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

    response = client.get(
        f"/structure/jobs/{job_id}/download/datasets/does-not-exist", headers=auth_headers
    )
    assert response.status_code == 404


def test_download_invalid_collection_returns_400(client: TestClient, auth_headers: dict[str, str]) -> None:
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

    response = client.get(
        f"/structure/jobs/{job_id}/download/not-a-real-collection/whatever", headers=auth_headers
    )
    assert response.status_code == 400


def test_download_report_returns_pdf(client: TestClient, auth_headers: dict[str, str]) -> None:
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

    response = client.get(f"/structure/jobs/{job_id}/report", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_download_endpoints_require_authentication(client: TestClient) -> None:
    table_response = client.get("/structure/jobs/irrelevant/download/tables/whatever")
    report_response = client.get("/structure/jobs/irrelevant/report")
    assert table_response.status_code == 401
    assert report_response.status_code == 401


def test_download_endpoints_return_409_before_completion(
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

    status_response = client.get(f"/structure/jobs/{job_id}", headers=auth_headers)
    if status_response.json()["status"] not in ("completed", "failed"):
        report_response = client.get(f"/structure/jobs/{job_id}/report", headers=auth_headers)
        assert report_response.status_code == 409

    _wait_for_completion(client, job_id, auth_headers)