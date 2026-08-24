"""
synclair_structure.services.clustering_metrics_service
---------------------------------------------------------------

Orchestrates the core clustering metrics in a single call. Migrated
from the legacy compute_all_cluster_metrics function; composes
SilhouetteMetric, DaviesBouldinMetric, InertiaMetric, and (optionally)
AdjustedRandIndexMetric by dependency injection rather than duplicating
their logic. This is a composition/orchestration service, not a single
metric, so it lives in services/ rather than metrics/.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from synclair_structure.metrics.adjusted_rand_index import AdjustedRandIndexMetric
from synclair_structure.metrics.davies_bouldin import DaviesBouldinMetric
from synclair_structure.metrics.inertia import InertiaMetric
from synclair_structure.metrics.silhouette import SilhouetteMetric

__all__ = ["ClusteringMetricsService"]


class ClusteringMetricsService:
    """Computes the standard set of clustering metrics in one pass."""

    def __init__(
        self,
        silhouette_metric: SilhouetteMetric | None = None,
        davies_bouldin_metric: DaviesBouldinMetric | None = None,
        inertia_metric: InertiaMetric | None = None,
        adjusted_rand_index_metric: AdjustedRandIndexMetric | None = None,
    ) -> None:
        self._silhouette_metric = silhouette_metric or SilhouetteMetric()
        self._davies_bouldin_metric = davies_bouldin_metric or DaviesBouldinMetric()
        self._inertia_metric = inertia_metric or InertiaMetric()
        self._adjusted_rand_index_metric = adjusted_rand_index_metric or AdjustedRandIndexMetric()

    def compute_all(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        labels_true: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Compute silhouette, Davies-Bouldin, inertia, n_clusters, noise_ratio,
        and (if `labels_true` is given) the Adjusted Rand Index.
        """
        results: dict[str, Any] = {
            "silhouette": self._silhouette_metric.compute(X, labels),
            "davies_bouldin": self._davies_bouldin_metric.compute(X, labels),
            "inertia": self._inertia_metric.compute(X, labels),
            "n_clusters": len(np.unique(labels[labels != -1])),
            "noise_ratio": float(np.mean(labels == -1)) if -1 in labels else 0.0,
        }

        if labels_true is not None:
            results["adjusted_rand_index"] = self._adjusted_rand_index_metric.compute(labels_true, labels)

        return results