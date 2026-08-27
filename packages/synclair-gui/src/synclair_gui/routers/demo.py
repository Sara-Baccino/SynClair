"""
synclair_gui.routers.demo
--------------------------------

Public, unauthenticated demo endpoints. Structure can be run either
against a named toy dataset (Iris/Wine) or against an inline dataset
(columns+rows) supplied by the caller -- the latter is what allows the
frontend to chain "artifact of a previous demo run -> input of the
next", entirely client-side, with zero server-side state.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from synclair_core.dataset.config_builder import ConfigBuilder
from synclair_core.models.analysis_result import AnalysisResult
from synclair_core.pipeline.base_pipeline import BasePipeline

from synclair_gui.services.demo_datasets import (
    DEMO_DATASETS,
    DemoDatasetNotFoundError,
    get_demo_dataset,
    summarize_dataset,
    summarize_columns,
)

from synclair_structure.config.clustering_configs import KMeansConfig
from synclair_structure.config.projection_configs import PCAConfig
from synclair_structure.config.structure_module_config import StructureModuleConfig
from synclair_structure.pipeline.structure_module import StructureModule

__all__ = ["router"]

router = APIRouter(prefix="/demo", tags=["demo"])

DemoDatasetName = Literal["iris", "wine"]


# ---------------------------------------------------------------------- #
# DTOs
# ---------------------------------------------------------------------- #
class DemoToolDTO(BaseModel):
    id: str
    title: str
    description: str


class DemoToolsResponse(BaseModel):
    tools: list[DemoToolDTO]
    demo_datasets: list[DemoDatasetDTO]


class DemoColumnSummaryDTO(BaseModel):
    name: str
    numerical: bool
    categorical: bool


class DemoDatasetDTO(BaseModel):
    name: str
    title: str
    description: str
    n_rows: int
    n_columns: int
    n_numerical: int
    n_categorical: int
    columns: list[DemoColumnSummaryDTO]

    
class InlineDatasetDTO(BaseModel):
    """A dataset supplied inline by the caller -- e.g. an artifact from a
    previous demo run, kept only in the browser and never persisted
    server-side. Validated for basic shape consistency before use.
    """

    columns: list[str] = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(min_length=1)


class DemoStructureRunRequest(BaseModel):
    dataset_name: DemoDatasetName | None = Field(
        default=None,
        description="One of the predefined public demo datasets. Mutually exclusive with inline_dataset.",
    )
    inline_dataset: InlineDatasetDTO | None = Field(
        default=None,
        description="A caller-supplied dataset (e.g. a previous demo run's artifact), used instead of dataset_name.",
    )
    excluded_columns: list[str] = Field(default_factory=list)
    n_clusters: int = Field(default=3, ge=2, le=8)
    include_projection: bool = Field(default=True)

    @model_validator(mode="after")
    def _check_exactly_one_source(self) -> "DemoStructureRunRequest":
        if bool(self.dataset_name) == bool(self.inline_dataset):
            raise ValueError("Exactly one of dataset_name or inline_dataset must be provided.")
        return self


class EmbeddingPointDTO(BaseModel):
    x: float
    y: float


class DemoStructureRunResponse(BaseModel):
    dataset_label: str
    n_observations: int
    n_features: int
    feature_names: list[str]
    labels: list[int]
    metrics: dict[str, float | int | str | bool]
    embedding: list[EmbeddingPointDTO] | None
    clustered_rows: list[dict[str, Any]]
    """Full clustered dataset (feature columns + cluster_label), small
    enough for toy datasets to return in full -- this is what the
    frontend uses to build an AnalysisInputSource for chaining."""
    success: bool
    error: str | None


# ---------------------------------------------------------------------- #
# Endpoints
# ---------------------------------------------------------------------- #
@router.get("/tools", response_model=DemoToolsResponse)
def list_demo_tools() -> DemoToolsResponse:
    tools = [DemoToolDTO(id="structure", title="Structure Discovery", description="Clustering, dimensionality reduction, and structure discovery on your data.")]
    demo_datasets = []
    for dataset in DEMO_DATASETS.values():
        summary = summarize_dataset(dataset)
        columns = summarize_columns(dataset)
        demo_datasets.append(
            DemoDatasetDTO(
                name=summary.name, title=summary.title, description=summary.description,
                n_rows=summary.n_rows, n_columns=summary.n_columns,
                n_numerical=summary.n_numerical, n_categorical=summary.n_categorical,
                columns=[{"name": c.name, "numerical": c.numerical, "categorical": c.categorical} for c in columns],
            )
        )
    return DemoToolsResponse(tools=tools, demo_datasets=demo_datasets)


@router.post("/structure/run", response_model=DemoStructureRunResponse)
def run_demo_structure(request: DemoStructureRunRequest) -> DemoStructureRunResponse:
    if request.dataset_name is not None:
        try:
            demo_dataset = get_demo_dataset(request.dataset_name)
        except DemoDatasetNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        dataframe = demo_dataset.build()
        dataset_label = demo_dataset.title
    else:
        inline = request.inline_dataset
        try:
            dataframe = pl.DataFrame(inline.rows).select(inline.columns)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid inline_dataset: {exc}") from exc
        dataset_label = "Previous analysis output"

    # Rimuove le colonne escluse direttamente dal Polars DataFrame
    if request.excluded_columns:
        cols_to_drop = [c for c in request.excluded_columns if c in dataframe.columns]
        if cols_to_drop:
            dataframe = dataframe.drop(cols_to_drop)

    data_config = ConfigBuilder.build_config(dataframe, infer_id=False)

    module_config = StructureModuleConfig(
        clustering_algorithm="kmeans",
        clustering_config=KMeansConfig(n_clusters=request.n_clusters, random_state=42),
        projection_algorithm="pca" if request.include_projection else "none",
        projection_config=PCAConfig(n_components=2) if request.include_projection else None,
    )

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    dataframe.write_parquet(tmp_path)

    try:
        pipeline = BasePipeline(
            module=StructureModule(),
            dataset_path=tmp_path,
            data_config=data_config,
            module_config=module_config,
            apply_imputation=False,
        )
        result: AnalysisResult = pipeline.run()
    finally:
        tmp_path.unlink(missing_ok=True)

    return _analysis_result_to_demo_response(dataset_label, dataframe, result)
def _analysis_result_to_demo_response(
    dataset_label: str, dataframe: pl.DataFrame, result: AnalysisResult
) -> DemoStructureRunResponse:
    if not result.success:
        return DemoStructureRunResponse(
            dataset_label=dataset_label,
            n_observations=dataframe.height,
            n_features=dataframe.width,
            feature_names=dataframe.columns,
            labels=[],
            metrics={},
            embedding=None,
            clustered_rows=[],
            success=False,
            error=result.error,
        )

    clustered = result.datasets.get("clustered_dataset")
    labels = clustered["cluster_label"].to_list() if clustered is not None else []
    clustered_rows = clustered.to_dicts() if clustered is not None else []

    embedding_df = result.datasets.get("projection_embedding")
    embedding: list[EmbeddingPointDTO] | None = None
    if embedding_df is not None and embedding_df.width >= 2:
        first_two = embedding_df.columns[:2]
        embedding = [
            EmbeddingPointDTO(x=row[0], y=row[1]) for row in embedding_df.select(first_two).iter_rows()
        ]

    return DemoStructureRunResponse(
        dataset_label=dataset_label,
        n_observations=dataframe.height,
        n_features=dataframe.width,
        feature_names=dataframe.columns,
        labels=labels,
        metrics=result.metrics,
        embedding=embedding,
        clustered_rows=clustered_rows,
        success=True,
        error=None,
    )
