"""
synclair_gui.routers.demo
--------------------------------

Public, unauthenticated demo endpoints for the landing page: list
available tools/demo datasets, and run StructureModule synchronously
against one of a small, fixed set of server-defined synthetic datasets.

Deliberately anonymous, stateless, and synchronous:
- no dataset_store / job_manager interaction (nothing persisted, no
  workspace record created, no polling);
- no authentication dependency (unlike datasets.py/structure.py);
- dataset selection is restricted to a Literal enum validated at the
  schema level, never an arbitrary path or upload;
- the clustering algorithm is fixed (kmeans) and only a couple of safe,
  bounded parameters are exposed to the caller -- no arbitrary
  StructureModuleConfig from user input.

This router does not reimplement any clustering/projection logic: it
builds a StructureModuleConfig, runs the exact same BasePipeline +
StructureModule used by the authenticated Workspace (routers/structure.py),
and adapts the resulting AnalysisResult into a minimal response DTO.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from synclair_core.dataset.config_builder import ConfigBuilder
from synclair_core.models.analysis_result import AnalysisResult
from synclair_core.pipeline.base_pipeline import BasePipeline

from synclair_gui.services.demo_datasets import (
    DEMO_DATASETS,
    DemoDatasetNotFoundError,
    get_demo_dataset,
)

from synclair_structure.config.clustering_configs import KMeansConfig
from synclair_structure.config.projection_configs import PCAConfig
from synclair_structure.config.structure_module_config import StructureModuleConfig
from synclair_structure.pipeline.structure_module import StructureModule

__all__ = ["router"]

router = APIRouter(prefix="/demo", tags=["demo"])

DemoDatasetName = Literal["blobs_2d", "elongated_clusters", "clinical_like"]


# ---------------------------------------------------------------------- #
# DTOs
# ---------------------------------------------------------------------- #
class DemoToolDTO(BaseModel):
    id: str
    title: str
    description: str


class DemoDatasetDTO(BaseModel):
    name: str
    title: str
    description: str


class DemoToolsResponse(BaseModel):
    tools: list[DemoToolDTO]
    demo_datasets: list[DemoDatasetDTO]


class DemoStructureRunRequest(BaseModel):
    dataset_name: DemoDatasetName = Field(
        description="One of the predefined, public demo datasets. No other value is accepted."
    )
    n_clusters: int = Field(default=3, ge=2, le=8)
    include_projection: bool = Field(
        default=True, description="Whether to also run a 2D PCA projection for visualization."
    )


class EmbeddingPointDTO(BaseModel):
    x: float
    y: float


class DemoStructureRunResponse(BaseModel):
    dataset_name: str
    n_observations: int
    n_features: int
    feature_names: list[str]
    labels: list[int]
    metrics: dict[str, float | int | str | bool]
    embedding: list[EmbeddingPointDTO] | None
    success: bool
    error: str | None


# ---------------------------------------------------------------------- #
# Endpoints
# ---------------------------------------------------------------------- #
@router.get("/tools", response_model=DemoToolsResponse)
def list_demo_tools() -> DemoToolsResponse:
    """Public, unauthenticated: lists tools and demo datasets for the landing page."""
    tools = [
        DemoToolDTO(
            id="structure",
            title="Structure Discovery",
            description="Clustering, dimensionality reduction, and structure discovery on your data.",
        ),
    ]
    demo_datasets = [
        DemoDatasetDTO(name=dataset.name, title=dataset.title, description=dataset.description)
        for dataset in DEMO_DATASETS.values()
    ]
    return DemoToolsResponse(tools=tools, demo_datasets=demo_datasets)


@router.post("/structure/run", response_model=DemoStructureRunResponse)
def run_demo_structure(request: DemoStructureRunRequest) -> DemoStructureRunResponse:
    """Public, unauthenticated, stateless, synchronous demo of StructureModule.

    Runs the same BasePipeline + StructureModule used by the
    authenticated Workspace (routers/structure.py) against a fixed,
    server-defined synthetic dataset. Never touches dataset_store or
    job_manager: no state from this call persists or is associated with
    any user.
    """
    try:
        demo_dataset = get_demo_dataset(request.dataset_name)
    except DemoDatasetNotFoundError as exc:
        # Unreachable in practice: DemoDatasetName already restricts the
        # schema to known values, so pydantic rejects anything else with
        # a 422 before this handler runs. Kept as defense in depth.
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    dataframe = demo_dataset.build()
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

    return _analysis_result_to_demo_response(request.dataset_name, dataframe, result)


# ---------------------------------------------------------------------- #
# Adapter: AnalysisResult -> minimal public DTO. No scientific logic
# lives here, only field extraction of what StructureModule already
# computed.
# ---------------------------------------------------------------------- #
def _analysis_result_to_demo_response(
    dataset_name: str, dataframe: pl.DataFrame, result: AnalysisResult
) -> DemoStructureRunResponse:
    if not result.success:
        return DemoStructureRunResponse(
            dataset_name=dataset_name,
            n_observations=dataframe.height,
            n_features=dataframe.width,
            feature_names=dataframe.columns,
            labels=[],
            metrics={},
            embedding=None,
            success=False,
            error=result.error,
        )

    clustered = result.datasets.get("clustered_dataset")
    labels = clustered["cluster_label"].to_list() if clustered is not None else []

    embedding_df = result.datasets.get("projection_embedding")
    embedding: list[EmbeddingPointDTO] | None = None
    if embedding_df is not None and embedding_df.width >= 2:
        first_two_columns = embedding_df.columns[:2]
        embedding = [
            EmbeddingPointDTO(x=row[0], y=row[1])
            for row in embedding_df.select(first_two_columns).iter_rows()
        ]

    return DemoStructureRunResponse(
        dataset_name=dataset_name,
        n_observations=dataframe.height,
        n_features=dataframe.width,
        feature_names=dataframe.columns,
        labels=labels,
        metrics=result.metrics,
        embedding=embedding,
        success=True,
        error=None,
    )