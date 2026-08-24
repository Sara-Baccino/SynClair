"""
synclair_structure.config.clustering_configs
------------------------------------------------

Pydantic configuration objects for every clustering algorithm. Each
config describes only algorithm parameters (never data or columns),
mirroring the legacy functions' `cfg.get(...)` defaults exactly.
`extra_params` preserves the legacy behaviour of forwarding any
additional sklearn/hdbscan/skfuzzy kwarg not explicitly modeled here.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "HDBSCANConfig",
    "KMeansConfig",
    "AgglomerativeConfig",
    "GMMConfig",
    "FuzzyCMeansConfig",
]


class HDBSCANConfig(BaseModel):
    """Configuration for HDBSCANAlgorithm. Mirrors run_hdbscan's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    min_cluster_size: int = 15
    min_samples: int | None = None
    metric: str = "euclidean"
    cluster_selection_method: Literal["eom", "leaf"] = "eom"
    extra_params: dict[str, Any] = Field(default_factory=dict)


class KMeansConfig(BaseModel):
    """Configuration for KMeansAlgorithm. Mirrors run_kmeans's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_clusters: int = 5
    init: str = "k-means++"
    n_init: int | str = 10
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class AgglomerativeConfig(BaseModel):
    """Configuration for AgglomerativeAlgorithm. Mirrors run_agglomerative's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_clusters: int = 5
    metric: str = "euclidean"
    linkage: Literal["ward", "complete", "average", "single"] = "ward"
    extra_params: dict[str, Any] = Field(default_factory=dict)


class GMMConfig(BaseModel):
    """Configuration for GaussianMixtureAlgorithm. Mirrors run_gmm's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 5
    covariance_type: Literal["full", "tied", "diag", "spherical"] = "full"
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class FuzzyCMeansConfig(BaseModel):
    """Configuration for FuzzyCMeansAlgorithm. Mirrors run_fuzzy_cmeans's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_clusters: int = 5
    m: float = Field(default=2.0, description="Fuzziness index.")
    error: float = 0.005
    maxiter: int = 1000
    init: Any = None
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)