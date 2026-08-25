"""
Tests for JobManager: state transitions, thread-safety under concurrent
job execution, progress reporting, and failure handling.
"""

import threading
import time

import pytest

from synclair_gui.services.job_manager import JobManager, JobNotFoundError, JobStatus


def test_create_job_starts_pending() -> None:
    manager = JobManager()
    job_id = manager.create_job()

    record = manager.get_job(job_id)
    assert record.status == JobStatus.PENDING
    assert record.result is None
    assert record.error is None


def test_run_job_success_transitions_to_completed() -> None:
    manager = JobManager()
    job_id = manager.create_job()

    def target(reporter):
        reporter.update("Step 1...", percentage=25.0)
        reporter.update("Step 2...", percentage=75.0)
        return {"answer": 42}

    manager.run_job(job_id, target)

    record = manager.get_job(job_id)
    assert record.status == JobStatus.COMPLETED
    assert record.result == {"answer": 42}
    assert record.progress.percentage == 100.0
    assert record.progress.logs == ["Step 1...", "Step 2..."]


def test_run_job_failure_transitions_to_failed_with_traceback() -> None:
    manager = JobManager()
    job_id = manager.create_job()

    def target(reporter):
        reporter.update("About to fail...")
        raise ValueError("boom")

    manager.run_job(job_id, target)

    record = manager.get_job(job_id)
    assert record.status == JobStatus.FAILED
    assert record.result is None
    assert "ValueError: boom" in record.error


def test_get_unknown_job_raises_not_found() -> None:
    manager = JobManager()
    with pytest.raises(JobNotFoundError):
        manager.get_job("does-not-exist")


def test_get_job_returns_a_copy_not_a_live_reference() -> None:
    manager = JobManager()
    job_id = manager.create_job()

    snapshot = manager.get_job(job_id)
    manager.run_job(job_id, lambda reporter: "done")

    # The earlier snapshot must not have been mutated in place.
    assert snapshot.status == JobStatus.PENDING
    assert manager.get_job(job_id).status == JobStatus.COMPLETED


def test_concurrent_jobs_do_not_corrupt_each_other_state() -> None:
    manager = JobManager()
    job_ids = [manager.create_job() for _ in range(10)]

    def target_factory(index: int):
        def target(reporter):
            time.sleep(0.01)
            reporter.update(f"job {index} progressing")
            return index
        return target

    threads = [
        threading.Thread(target=manager.run_job, args=(job_id, target_factory(i)))
        for i, job_id in enumerate(job_ids)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for i, job_id in enumerate(job_ids):
        record = manager.get_job(job_id)
        assert record.status == JobStatus.COMPLETED
        assert record.result == i