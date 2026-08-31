"""
synclair_gui.routers.datasets
------------------------------------

Endpoints for Workspace Step 1: dataset upload and DataConfig
build/validation. Wraps synclair-core's Loader and ConfigBuilder behind
explicit DTOs, so the API contract stays stable even if the internal
DataConfig/ColumnInfo models evolve. Protected by JWT authentication:
every endpoint here requires a valid bearer token (see auth.py).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from synclair_core.dataset.config_builder import ConfigBuilder
from synclair_core.dataset.config_reader import ConfigReader
from synclair_core.dataset.loader import Loader
from synclair_core.exceptions import ConfigParseError, DatasetLoadError
from synclair_core.models.column_info import ColumnInfo
from synclair_core.models.data_config import DataConfig
from synclair_core.models.analysis_result import AnalysisResult

from synclair_gui.routers.auth import CurrentUserResponse, get_current_user
from synclair_gui.services.dataset_store import DatasetNotFoundError, dataset_store
from synclair_gui.services.job_manager import JobNotFoundError, JobStatus, job_manager



__all__ = ["router"]

router = APIRouter(prefix="/datasets", tags=["datasets"])


# ---------------------------------------------------------------------- #
# DTOs -- deliberately explicit, not a passthrough of the core models
# ---------------------------------------------------------------------- #
class ColumnPreviewDTO(BaseModel):
    name: str
    dtype: str


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int
    n_columns: int
    columns: list[ColumnPreviewDTO]
    preview: list[dict[str, Any]] = Field(description="First rows of the dataset, JSON-safe.")


class MissingDataManagementDTO(BaseModel):
    strategy: str
    value: Any | None = None
    condition: list[Any]
    imputer: str


class ScalingConfigDTO(BaseModel):
    enabled: bool
    method: str


class EncodingConfigDTO(BaseModel):
    enabled: bool
    method: str
    order: list[Any] | None = None


class ColumnInfoDTO(BaseModel):
    name: str
    new_name: str
    active: bool
    categorical: bool
    numerical: bool
    id: bool
    semantic_roles: list[str]
    multiplier: float
    mappings: dict[str, Any]
    missing_data_management: MissingDataManagementDTO
    scaling: ScalingConfigDTO
    encoding: EncodingConfigDTO
    type: str | None


class DataConfigDTO(BaseModel):
    columns: list[ColumnInfoDTO]


class ConfigValidationDTO(BaseModel):
    is_valid: bool
    missing_in_dataset: list[str]
    unconfigured_in_dataset: list[str]
    errors: list[str]


class ParseConfigRequest(BaseModel):
    dataset_id: str
    existing_config: dict[str, Any] | None = Field(
        default=None,
        description=(
            "A previously built/edited DataConfig payload (as returned by this "
            "same endpoint, or hand-edited by the frontend) to re-validate. If "
            "omitted, a new DataConfig is built from scratch via ConfigBuilder."
        ),
    )
    id_columns: list[str] | None = None
    infer_id: bool = True
    custom_id_patterns: list[str] | None = None


class ParseConfigResponse(BaseModel):
    dataset_id: str
    data_config: DataConfigDTO
    validation: ConfigValidationDTO


# ---------------------------------------------------------------------- #
# Mapping helpers: core models -> DTOs
# ---------------------------------------------------------------------- #
def _column_info_to_dto(name: str, info: ColumnInfo) -> ColumnInfoDTO:
    return ColumnInfoDTO(
        name=name,
        new_name=info.new_name,
        active=info.active,
        categorical=info.categorical,
        numerical=info.numerical,
        id=info.id,
        semantic_roles=sorted(info.semantic_roles),
        multiplier=info.multiplier,
        mappings=info.mappings,
        missing_data_management=MissingDataManagementDTO(
            strategy=info.missing_data_management.strategy.value,
            value=info.missing_data_management.value,
            condition=info.missing_data_management.condition,
            imputer=info.missing_data_management.imputer.value,
        ),
        scaling=ScalingConfigDTO(
            enabled=info.scaling.enabled,
            method=info.scaling.method.value,
        ),
        encoding=EncodingConfigDTO(
            enabled=info.encoding.enabled,
            method=info.encoding.method.value,
            order=info.encoding.order,
        ),
        type=info.type.value if info.type is not None else None,
    )


def _data_config_to_dto(config: DataConfig) -> DataConfigDTO:
    return DataConfigDTO(columns=[_column_info_to_dto(name, info) for name, info in config.items()])


# ---------------------------------------------------------------------- #
# Endpoints
# ---------------------------------------------------------------------- #
@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> DatasetUploadResponse:
    """Upload a CSV/Parquet/etc. file, load it via synclair-core's Loader,
    and register it in the in-memory dataset store. Requires authentication.
    """
    original_name = file.filename or "dataset"
    extension = Path(original_name).suffix.lower()

    if extension not in Loader.supported_extensions():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{extension}'. Supported: {Loader.supported_extensions()}",
        )

    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp_file:
        tmp_file.write(contents)
        tmp_path = Path(tmp_file.name)

    try:
        dataframe = Loader.load(tmp_path)
    except DatasetLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    record = dataset_store.add(filename=original_name, dataframe=dataframe)

    columns = [
        ColumnPreviewDTO(name=col_name, dtype=str(dataframe.schema[col_name]))
        for col_name in dataframe.columns
    ]
    preview = dataframe.head(5).to_dicts()

    return DatasetUploadResponse(
        dataset_id=record.dataset_id,
        filename=record.filename,
        n_rows=dataframe.height,
        n_columns=dataframe.width,
        columns=columns,
        preview=preview,
    )


@router.post("/parse-config", response_model=ParseConfigResponse)
def parse_config(
    request: ParseConfigRequest,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> ParseConfigResponse:
    """Build (or re-validate) a DataConfig for a previously uploaded dataset.
    Requires authentication.
    """
    try:
        record = dataset_store.get(request.dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if request.existing_config is not None:
        try:
            data_config = ConfigReader.from_dict(request.existing_config)
        except ConfigParseError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    else:
        data_config = ConfigBuilder.build_config(
            record.dataframe,
            id_columns=request.id_columns,
            infer_id=request.infer_id,
            custom_id_patterns=request.custom_id_patterns,
        )

    validation = ConfigBuilder.validate_config(record.dataframe, data_config)
    dataset_store.set_data_config(request.dataset_id, data_config)

    return ParseConfigResponse(
        dataset_id=request.dataset_id,
        data_config=_data_config_to_dto(data_config),
        validation=ConfigValidationDTO(
            is_valid=validation.is_valid,
            missing_in_dataset=validation.missing_in_dataset,
            unconfigured_in_dataset=validation.unconfigured_in_dataset,
            errors=validation.errors,
        ),
    )

# --- nuovo DTO, vicino agli altri DTO del file ---
class DatasetDetailResponse(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int
    n_columns: int
    has_data_config: bool


# --- nuovo endpoint, dopo parse_config ---
@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> DatasetDetailResponse:
    """Read-only existence/state check for a dataset, used by the frontend's
    DatasetGuard to verify against real backend state (not just local
    frontend context) whether a dataset_id is still valid -- e.g. after a
    page refresh or back/forward navigation.
    """
    try:
        record = dataset_store.get(dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DatasetDetailResponse(
        dataset_id=record.dataset_id,
        filename=record.filename,
        n_rows=record.dataframe.height,
        n_columns=record.dataframe.width,
        has_data_config=record.data_config is not None,
    )

class RowFilterCondition(BaseModel):
    column: str
    operator: Literal["eq", "ne", "in", "not_in", "gt", "gte", "lt", "lte"]
    value: Any


class FromArtifactRequest(BaseModel):
    source_job_id: str
    artifact_name: str = Field(description="Key in AnalysisResult.datasets to promote (e.g. 'clustered_dataset', 'matched_dataset').")
    row_filters: list[RowFilterCondition] = Field(default_factory=list)
    new_filename: str | None = None


def _apply_row_filter(dataframe, condition: RowFilterCondition):
    import polars as pl

    if condition.column not in dataframe.columns:
        raise ValueError(f"Column '{condition.column}' not found.")

    dtype = dataframe.schema[condition.column]
    value = condition.value

    # Frontend filter UI necessarily works with stringified preview
    # values (HTML checkboxes have string values); cast them back to
    # the real column dtype before filtering, instead of requiring the
    # frontend to know Polars types.
    if condition.operator in ("in", "not_in") and isinstance(value, list):
        value = pl.Series(value).cast(dtype, strict=False).to_list()
    else:
        value = pl.Series([value]).cast(dtype, strict=False).to_list()[0]

    col = pl.col(condition.column)
    op_map = {
        "eq": col == value, "ne": col != value,
        "in": col.is_in(value), "not_in": ~col.is_in(value),
        "gt": col > value, "gte": col >= value, "lt": col < value, "lte": col <= value,
    }
    return dataframe.filter(op_map[condition.operator])


@router.post("/from-artifact", response_model=DatasetUploadResponse)
def create_dataset_from_artifact(
    request: FromArtifactRequest,
    current_user: CurrentUserResponse = Depends(get_current_user),
) -> DatasetUploadResponse:
    """Promote an artifact (a pl.DataFrame in AnalysisResult.datasets)
    from a completed job -- of ANY module -- into a new dataset in
    dataset_store, so it can be configured and analyzed like any
    uploaded dataset. Deliberately module-agnostic: reads AnalysisResult
    generically, never imports a concrete module type, so this works
    identically whether the source job was Structure, Matching, or any
    future module. Requires authentication.
    """
    try:
        record = job_manager.get_job(request.source_job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job '{request.source_job_id}' is not completed (status='{record.status.value}').",
        )

    result: AnalysisResult = record.result
    if not result.success:
        raise HTTPException(status_code=409, detail="Source job did not complete successfully.")

    dataframe = result.datasets.get(request.artifact_name)
    if dataframe is None:
        raise HTTPException(
            status_code=404,
            detail=f"No artifact named '{request.artifact_name}' found in job '{request.source_job_id}'. "
                   f"Available: {sorted(result.datasets.keys())}",
        )

    for condition in request.row_filters:
        if condition.column not in dataframe.columns:
            raise HTTPException(status_code=422, detail=f"row_filter column '{condition.column}' not found in artifact.")
        try:
            dataframe = _apply_row_filter(dataframe, condition)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid row_filter for column '{condition.column}': {exc}") from exc

    if dataframe.height == 0:
        raise HTTPException(status_code=422, detail="row_filters produced an empty dataset.")

    filename = request.new_filename or f"{request.artifact_name}__from_{request.source_job_id[:8]}"
    new_record = dataset_store.add(filename=filename, dataframe=dataframe)

    columns = [
        ColumnPreviewDTO(name=col_name, dtype=str(dataframe.schema[col_name]))
        for col_name in dataframe.columns
    ]
    preview = dataframe.head(5).to_dicts()

    return DatasetUploadResponse(
        dataset_id=new_record.dataset_id,
        filename=new_record.filename,
        n_rows=dataframe.height,
        n_columns=dataframe.width,
        columns=columns,
        preview=preview,
    )