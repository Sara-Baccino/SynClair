from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
 
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from pydantic import BaseModel, Field, ValidationError

from synclair_core.models.analysis_result import AnalysisResult
from synclair_core.pipeline.base_pipeline import BasePipeline

from synclair_gui.routers.auth import CurrentUserResponse, get_current_user
from synclair_gui.services.dataset_store import DatasetNotFoundError, dataset_store
from synclair_gui.services.job_manager import (
    JobNotFoundError,
    JobProgressReporter,
    JobStatus,
    job_manager,
)

from synclair_structure.config.structure_module_config import StructureModuleConfig
from synclair_structure.pipeline.structure_module import StructureModule

from synclair_reporting.report_manager import ReportManager

__all__ = ["router"]


router = APIRouter(prefix="/structure", tags=["structure"])

_PREVIEW_ROW_LIMIT = 20


# ---------------------------------------------------------------------- #
# DTOs
# ---------------------------------------------------------------------- #
class StructureRunRequest(BaseModel):
    dataset_id: str
    module_config: dict[str, Any] = Field(
        description="Raw payload validated against StructureModuleConfig server-side."
    )


class StructureRunResponse(BaseModel):
    job_id: str


class JobProgressDTO(BaseModel):
    message: str
    percentage: float | None
    logs: list[str]


class StructureJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: JobProgressDTO


class DataFramePreviewDTO(BaseModel):
    name: str
    n_rows: int
    n_columns: int
    columns: list[str]
    preview: list[dict[str, Any]]


class StructureResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    success: bool
    error: str | None
    metrics: dict[str, float | int | str | bool]
    tables: list[DataFramePreviewDTO]
    datasets: list[DataFramePreviewDTO]
    runtime_seconds: float | None


# ---------------------------------------------------------------------- #
# Internal helpers
# ---------------------------------------------------------------------- #
def _serialize_validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Convert a pydantic ValidationError into a JSON-safe list of error dicts.

    pydantic's exc.errors() may include a 'ctx' entry containing the raw
    exception instance raised inside a model_validator (e.g. the
    ValueError from StructureModuleConfig's cross-field checks) rather
    than just its message. That instance is not JSON-serializable, so
    it is stringified here before the errors are handed to HTTPException.
    """
    serialized_errors = []
    for error in exc.errors(include_url=False):
        error = dict(error)
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error["ctx"] = {
                key: (str(value) if isinstance(value, BaseException) else value)
                for key, value in ctx.items()
            }
        serialized_errors.append(error)
    return serialized_errors


def _build_structure_job_target(
    dataset_id: str, module_config: StructureModuleConfig
):
    """Build the callable executed on the background thread by job_manager.

    Reuses BasePipeline for the full load->preprocess->execute flow: the
    in-memory dataframe already held by dataset_store is written to a
    temporary parquet file (BasePipeline.load_dataset expects a path),
    so no preprocessing sequence is reimplemented here.
    """

    def target(reporter: JobProgressReporter) -> AnalysisResult:
        reporter.update("Loading dataset and configuration...", percentage=5.0)
        record = dataset_store.get(dataset_id)
        if record.data_config is None:
            raise ValueError(
                f"Dataset '{dataset_id}' has no DataConfig yet. "
                "Call POST /datasets/parse-config before running structure analysis."
            )

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        record.dataframe.write_parquet(tmp_path)

        try:
            reporter.update("Running preprocessing and structure pipeline...", percentage=25.0)
            pipeline = BasePipeline(
                module=StructureModule(),
                dataset_path=tmp_path,
                data_config=record.data_config,
                module_config=module_config,
                apply_imputation=module_config.apply_imputation,
            )
            result = pipeline.run()
        finally:
            tmp_path.unlink(missing_ok=True)

        reporter.update("Structure pipeline finished.", percentage=95.0)
        return result

    return target


def _dataframe_to_preview_dto(name: str, dataframe) -> DataFramePreviewDTO:
    preview_rows = dataframe.head(_PREVIEW_ROW_LIMIT).to_dicts()
    return DataFramePreviewDTO(
        name=name,
        n_rows=dataframe.height,
        n_columns=dataframe.width,
        columns=dataframe.columns,
        preview=preview_rows,
    )


def _job_record_to_status_dto(job_id: str, record) -> StructureJobStatusResponse:
    return StructureJobStatusResponse(
        job_id=job_id,
        status=record.status,
        progress=JobProgressDTO(
            message=record.progress.message,
            percentage=record.progress.percentage,
            logs=record.progress.logs,
        ),
    )


# ---------------------------------------------------------------------- #
# Endpoints
# ---------------------------------------------------------------------- #
@router.post("/run", response_model=StructureRunResponse, status_code=202)
def run_structure_module(
    request: StructureRunRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> StructureRunResponse:
    """Start a StructureModule run for `dataset_id` as a background job.
    Requires authentication.

    Returns immediately with a job_id (HTTP 202 Accepted); poll
    GET /structure/jobs/{job_id} for progress and
    GET /structure/jobs/{job_id}/result once status == 'completed'.
    """
    try:
        dataset_store.get(request.dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        module_config = StructureModuleConfig.model_validate(request.module_config)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_serialize_validation_errors(exc)) from exc

    job_id = job_manager.create_job()
    target = _build_structure_job_target(request.dataset_id, module_config)
    background_tasks.add_task(job_manager.run_job, job_id, target)

    return StructureRunResponse(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=StructureJobStatusResponse)
def get_job_status(
    job_id: str,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> StructureJobStatusResponse:
    """Return the current status/progress of a structure job. Requires authentication."""
    try:
        record = job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _job_record_to_status_dto(job_id, record)


@router.get("/jobs/{job_id}/result", response_model=StructureResultResponse)
def get_job_result(
    job_id: str,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> StructureResultResponse:
    """Return a preview of the AnalysisResult produced by a completed job.
    Requires authentication.

    Raises 409 if the job hasn't completed yet (including if it failed
    before producing any result), so the frontend can distinguish "not
    ready" from "genuinely missing".
    """
    try:
        record = job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
        raise HTTPException(
            status_code=409,
            detail=f"Job '{job_id}' is not finished yet (status='{record.status.value}').",
        )

    if record.status == JobStatus.FAILED:
        return StructureResultResponse(
            job_id=job_id,
            status=record.status,
            success=False,
            error=record.error,
            metrics={},
            tables=[],
            datasets=[],
            runtime_seconds=None,
        )

    result: AnalysisResult = record.result
    return StructureResultResponse(
        job_id=job_id,
        status=record.status,
        success=result.success,
        error=result.error,
        metrics=result.metrics,
        tables=[_dataframe_to_preview_dto(name, df) for name, df in result.tables.items()],
        datasets=[_dataframe_to_preview_dto(name, df) for name, df in result.datasets.items()],
        runtime_seconds=result.runtime_seconds,
    )
# --- nuovi endpoint, aggiunti dopo get_job_result ---

@router.get("/jobs/{job_id}/download/{collection}/{name}")
def download_dataframe(
    job_id: str,
    collection: str,
    name: str,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> StreamingResponse:
    """Download a full (non-truncated) table or dataset produced by a
    completed job, as CSV. `collection` is either 'tables' or 'datasets',
    `name` must match a key actually present in the AnalysisResult --
    both are validated against the real job data, never used as a raw
    filesystem path.
    """
    try:
        record = job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"Job '{job_id}' is not completed yet.")

    result: AnalysisResult = record.result
    if collection == "tables":
        source = result.tables
    elif collection == "datasets":
        source = result.datasets
    else:
        raise HTTPException(status_code=400, detail="collection must be 'tables' or 'datasets'.")

    dataframe = source.get(name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail=f"No '{name}' found in {collection} for this job.")

    csv_bytes = dataframe.write_csv().encode("utf-8")
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{name}.csv"'},
    )


@router.get("/jobs/{job_id}/report")
def download_report(
    job_id: str,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> FileResponse:
    """Generate and download a PDF report for a completed job, via
    synclair-reporting's ReportManager (Phase 5) -- no report-generation
    logic is duplicated here, this endpoint is a thin HTTP adapter.
    """
    try:
        record = job_manager.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"Job '{job_id}' is not completed yet.")

    result: AnalysisResult = record.result

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    ReportManager.generate_pdf(result, tmp_path, title=f"Structure Analysis Report ({job_id})")

    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename=f"synclair-structure-report-{job_id}.pdf",
    )