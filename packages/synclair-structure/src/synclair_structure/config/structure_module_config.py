"""
synclair_structure.config.structure_module_config
-------------------------------------------------------

Aggregate module configuration for StructureModule: which clustering
algorithm to run (and its parameters), an optional projection step
ahead of clustering, whether to apply imputation, and optional
stability/explainability steps. clustering_algorithm/projection_algorithm
use Literal (validated at the type level, self-documenting) rather than
a free string resolved against a runtime registry.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from synclair_structure.config.clustering_configs import (
    AgglomerativeConfig,
    FuzzyCMeansConfig,
    GMMConfig,
    HDBSCANConfig,
    KMeansConfig,
)
from synclair_structure.config.explainability_configs import RFImportanceConfig, ShapConfig
from synclair_structure.config.projection_configs import (
    KernelPCAConfig,
    PaCMAPConfig,
    PCAConfig,
    SVDConfig,
    TSNEConfig,
    UMAPConfig,
)
from synclair_structure.config.stability_config import BootstrapStabilityConfig

__all__ = ["StructureModuleConfig"]

ClusteringAlgorithmName = Literal["hdbscan", "kmeans", "agglomerative", "gmm", "fuzzy_cmeans"]
ProjectionAlgorithmName = Literal["none", "pca", "umap", "tsne", "svd", "kernel_pca", "pacmap"]

ClusteringConfigUnion = HDBSCANConfig | KMeansConfig | AgglomerativeConfig | GMMConfig | FuzzyCMeansConfig
ProjectionConfigUnion = PCAConfig | UMAPConfig | TSNEConfig | SVDConfig | KernelPCAConfig | PaCMAPConfig

_CLUSTERING_CONFIG_TYPES: dict[str, type] = {
    "hdbscan": HDBSCANConfig,
    "kmeans": KMeansConfig,
    "agglomerative": AgglomerativeConfig,
    "gmm": GMMConfig,
    "fuzzy_cmeans": FuzzyCMeansConfig,
}

_PROJECTION_CONFIG_TYPES: dict[str, type] = {
    "pca": PCAConfig,
    "umap": UMAPConfig,
    "tsne": TSNEConfig,
    "svd": SVDConfig,
    "kernel_pca": KernelPCAConfig,
    "pacmap": PaCMAPConfig,
}


class StructureModuleConfig(BaseModel):
    """Module-specific configuration for StructureModule (clustering + friends)."""

    model_config = ConfigDict(extra="forbid")

    # --- Preprocessing hook, resolved by the caller from this field --- #
    apply_imputation: bool = False
    """Whether BasePipeline.preprocess() should run Imputation.fit_transform
    before this module runs (see Phase 3/4 discussion: imputation is not
    automatic, since profiling/discovery/cleaning modules need to observe
    residual nulls)."""

    # --- Clustering (required) --- #
    clustering_algorithm: ClusteringAlgorithmName
    clustering_config: ClusteringConfigUnion

    # --- Projection (optional, runs before clustering if set) --- #
    projection_algorithm: ProjectionAlgorithmName = "none"
    projection_config: ProjectionConfigUnion | None = None

    # --- Stability (optional) --- #
    run_stability: bool = False
    stability_config: BootstrapStabilityConfig = BootstrapStabilityConfig()

    # --- Explainability (optional, independently toggleable) --- #
    run_feature_importance: bool = False
    rf_importance_config: RFImportanceConfig = RFImportanceConfig()

    run_shap: bool = False
    shap_config: ShapConfig = ShapConfig()

    run_cluster_profile: bool = False

    @model_validator(mode="after")
    def _check_clustering_config_matches_algorithm(self) -> "StructureModuleConfig":
        expected_type = _CLUSTERING_CONFIG_TYPES[self.clustering_algorithm]
        if not isinstance(self.clustering_config, expected_type):
            raise ValueError(
                f"clustering_algorithm='{self.clustering_algorithm}' requires a "
                f"{expected_type.__name__}, got {type(self.clustering_config).__name__}."
            )
        return self

    @model_validator(mode="after")
    def _check_projection_config_matches_algorithm(self) -> "StructureModuleConfig":
        if self.projection_algorithm == "none":
            if self.projection_config is not None:
                raise ValueError("projection_config set but projection_algorithm == 'none'.")
            return self

        expected_type = _PROJECTION_CONFIG_TYPES[self.projection_algorithm]
        if not isinstance(self.projection_config, expected_type):
            raise ValueError(
                f"projection_algorithm='{self.projection_algorithm}' requires a "
                f"{expected_type.__name__}, got {type(self.projection_config).__name__ if self.projection_config else None}."
            )
        return self