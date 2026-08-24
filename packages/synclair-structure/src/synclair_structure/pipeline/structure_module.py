"""
synclair_structure.pipeline.structure_module
--------------------------------------------------

Concrete AnalysisModule for structure discovery: builds the numeric
feature matrix from the preprocessed dataset + DataConfig (resolving
one-hot columns via the fitted encoders in ExecutionContext), optionally
projects, clusters, computes clustering metrics, and optionally runs
stability/explainability. A local dict-based registry maps the Literal
algorithm name to its concrete class -- generalizing to a shared
PluginRegistry in synclair-core is deferred until synclair-matching
needs the same mechanism (migration plan decision #4).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from synclair_core.dataset.transformers import Transformers
from synclair_core.models.analysis_result import AnalysisResult, ResultMetadata
from synclair_core.models.column_info import EncoderType
from synclair_core.models.data_config import DataConfig
from synclair_core.pipeline.base_module import AnalysisModule
from synclair_core.pipeline.execution_context import ExecutionContext
from synclair_core.utils.io import save_analysis_result

from synclair_structure.algorithms.agglomerative_algorithm import AgglomerativeAlgorithm
from synclair_structure.algorithms.base import ClusteringAlgorithm
from synclair_structure.algorithms.fuzzy_cmeans_algorithm import FuzzyCMeansAlgorithm
from synclair_structure.algorithms.gmm_algorithm import GaussianMixtureAlgorithm
from synclair_structure.algorithms.hdbscan_algorithm import HDBSCANAlgorithm
from synclair_structure.algorithms.kmeans_algorithm import KMeansAlgorithm
from synclair_structure.config.structure_module_config import StructureModuleConfig
from synclair_structure.exceptions import StructureError
from synclair_structure.explainability.cluster_profiler import DescriptiveClusterProfiler
from synclair_structure.explainability.rf_importance import RandomForestImportanceExplainer
from synclair_structure.explainability.shap_explainer import ShapExplainer
from synclair_structure.projection.base import ProjectionAlgorithm
from synclair_structure.projection.kernel_pca import KernelPCAProjection
from synclair_structure.projection.pacmap_projection import PaCMAPProjection
from synclair_structure.projection.pca import PCAProjection
from synclair_structure.projection.svd import TruncatedSVDProjection
from synclair_structure.projection.tsne import TSNEProjection
from synclair_structure.projection.umap_projection import UMAPProjection
from synclair_structure.services.clustering_metrics_service import ClusteringMetricsService
from synclair_structure.stability.bootstrap import BootstrapStabilityEvaluator

__all__ = ["StructureModule"]

_CLUSTERING_REGISTRY: dict[str, type[ClusteringAlgorithm]] = {
    "hdbscan": HDBSCANAlgorithm,
    "kmeans": KMeansAlgorithm,
    "agglomerative": AgglomerativeAlgorithm,
    "gmm": GaussianMixtureAlgorithm,
    "fuzzy_cmeans": FuzzyCMeansAlgorithm,
}

_PROJECTION_REGISTRY: dict[str, type[ProjectionAlgorithm]] = {
    "pca": PCAProjection,
    "umap": UMAPProjection,
    "tsne": TSNEProjection,
    "svd": TruncatedSVDProjection,
    "kernel_pca": KernelPCAProjection,
    "pacmap": PaCMAPProjection,
}


class StructureModule(AnalysisModule[StructureModuleConfig]):
    """Clustering/structure-discovery analysis module."""

    def __init__(self, module_version: str | None = None) -> None:
        super().__init__(module_name="structure", module_version=module_version)
        self._result: AnalysisResult | None = None

    def fit(
        self,
        dataset: pl.DataFrame,
        data_config: DataConfig,
        module_config: StructureModuleConfig,
        context: ExecutionContext | None = None,
    ) -> "StructureModule":
        self._bind(dataset, data_config, module_config, context)
        return self

    def run(self) -> AnalysisResult:
        self._check_is_fitted()
        result = AnalysisResult(
            metadata=ResultMetadata(module_name=self.module_name, module_version=self.module_version)
        )

        try:
            X, feature_names = self._build_feature_matrix()
            working_X = X

            if self._module_config.projection_algorithm != "none":
                working_X = self._run_projection(X, result)

            labels = self._run_clustering(working_X, result)
            self._compute_metrics(working_X, labels, result)

            if self._module_config.run_stability:
                self._run_stability(working_X, result)

            if self._module_config.run_feature_importance:
                self._run_feature_importance(working_X, labels, feature_names, result)

            if self._module_config.run_shap:
                self._run_shap(working_X, labels, feature_names, result)

            if self._module_config.run_cluster_profile:
                self._run_cluster_profile(labels, feature_names, result)

            result.log("Structure module run completed successfully.")
        except Exception as exc:  # noqa: BLE001 - normalized into a failed AnalysisResult
            result.mark_failed(str(exc))

        self._result = result
        return result

    def save(self, folder: str | Path) -> None:
        """Persist the last run's AnalysisResult via synclair_core.utils.io
        (no dependency on synclair-reporting: reporting/GUI consume the
        resulting folder, they don't need to be known here).
        """
        if self._result is None:
            raise StructureError("save() called before run().")
        save_analysis_result(self._result, folder)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _build_feature_matrix(self) -> tuple[np.ndarray, list[str]]:
        """Select numerical columns plus any one-hot-expanded categorical
        columns as the feature matrix, resolving one-hot column names via
        the fitted encoders carried in ExecutionContext.
        """
        numeric_columns = self._data_config.numerical_columns()

        encoded_columns: list[str] = []
        for name, info in self._data_config.active_columns().items():
            if not info.encoding.enabled:
                continue
            if info.encoding.method == EncoderType.ONE_HOT:
                encoded_columns.extend(
                    Transformers.encoded_column_names(self._data_config, self._context.fitted_encoders, name)
                )
            else:  # ORDINAL: already a single numeric column
                encoded_columns.append(name)

        feature_names = numeric_columns + encoded_columns
        missing = [c for c in feature_names if c not in self._dataset.columns]
        if missing:
            raise StructureError(f"Feature columns missing from preprocessed dataset: {missing}")

        X = self._dataset.select(feature_names).to_numpy()
        return X, feature_names

    def _run_projection(self, X: np.ndarray, result: AnalysisResult) -> np.ndarray:
        algorithm = _PROJECTION_REGISTRY[self._module_config.projection_algorithm]()
        output = algorithm.fit_transform(X, self._module_config.projection_config)

        result.add_artifact("projection_model", output.model)
        result.add_dataset(
            "projection_embedding",
            pl.DataFrame(output.embedding, schema=[f"dim_{i}" for i in range(output.embedding.shape[1])]),
        )
        if output.explained_variance_ratio is not None:
            result.add_metric(
                "projection_explained_variance_total", float(np.sum(output.explained_variance_ratio))
            )
        return output.embedding

    def _run_clustering(self, X: np.ndarray, result: AnalysisResult) -> np.ndarray:
        algorithm = _CLUSTERING_REGISTRY[self._module_config.clustering_algorithm]()
        output = algorithm.fit_predict(X, self._module_config.clustering_config)

        result.add_artifact("clustering_model", output.model)
        result.add_dataset(
            "clustered_dataset", self._dataset.with_columns(pl.Series("cluster_label", output.labels))
        )
        if output.centers is not None:
            result.add_artifact("cluster_centers", output.centers)
        return output.labels

    def _compute_metrics(self, X: np.ndarray, labels: np.ndarray, result: AnalysisResult) -> None:
        service = ClusteringMetricsService()
        for name, value in service.compute_all(X, labels).items():
            result.add_metric(name, value)

    def _run_stability(self, X: np.ndarray, result: AnalysisResult) -> None:
        algorithm = _CLUSTERING_REGISTRY[self._module_config.clustering_algorithm]()

        def cluster_fn(data: np.ndarray) -> np.ndarray:
            return algorithm.fit_predict(data, self._module_config.clustering_config).labels

        evaluator = BootstrapStabilityEvaluator()
        output = evaluator.evaluate(X, cluster_fn, self._module_config.stability_config)

        result.add_metric("stability_mean_ari", output.mean_ari)
        result.add_metric("stability_std_ari", output.std_ari)
        result.add_artifact("stability_per_cluster_jaccard", output.per_cluster_jaccard_stability)

    def _run_feature_importance(
        self, X: np.ndarray, labels: np.ndarray, feature_names: list[str], result: AnalysisResult
    ) -> None:
        explainer = RandomForestImportanceExplainer()
        table = explainer.compute(X, labels, feature_names, self._module_config.rf_importance_config)
        result.add_table("feature_importance", table)

    def _run_shap(
        self, X: np.ndarray, labels: np.ndarray, feature_names: list[str], result: AnalysisResult
    ) -> None:
        explainer = ShapExplainer()
        output = explainer.compute(X, labels, feature_names, self._module_config.shap_config)
        result.add_artifact("shap_output", output)

    def _run_cluster_profile(self, labels: np.ndarray, feature_names: list[str], result: AnalysisResult) -> None:
        profiler = DescriptiveClusterProfiler()
        output = profiler.compute(self._dataset, labels, feature_names)
        result.add_table("cluster_means", output.cluster_means)
        result.add_table("cluster_medians", output.cluster_medians)
        result.add_table("cluster_z_scores", output.cluster_z_scores)