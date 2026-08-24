"""
synclair_structure.algorithms.hdbscan_algorithm
----------------------------------------------------

HDBSCAN clustering algorithm. Migrated from the legacy run_hdbscan
function; mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import hdbscan
import numpy as np

from synclair_structure.algorithms.base import ClusteringAlgorithm, ClusteringOutput
from synclair_structure.config.clustering_configs import HDBSCANConfig

__all__ = ["HDBSCANAlgorithm"]


class HDBSCANAlgorithm(ClusteringAlgorithm):
    """HDBSCAN clustering, delegating to the `hdbscan` package."""

    def fit_predict(self, X: np.ndarray, config: HDBSCANConfig) -> ClusteringOutput:
        model = hdbscan.HDBSCAN(
            min_cluster_size=config.min_cluster_size,
            min_samples=config.min_samples,
            metric=config.metric,
            cluster_selection_method=config.cluster_selection_method,
            **config.extra_params,
        )
        labels = model.fit_predict(X)

        return ClusteringOutput(
            labels=labels,
            model=model,
            probabilities=getattr(model, "probabilities_", None),
        )
    