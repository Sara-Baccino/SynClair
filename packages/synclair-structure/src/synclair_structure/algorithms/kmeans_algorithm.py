"""
synclair_structure.algorithms.kmeans_algorithm
---------------------------------------------------

KMeans clustering algorithm. Migrated from the legacy run_kmeans
function; mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from synclair_structure.algorithms.base import ClusteringAlgorithm, ClusteringOutput
from synclair_structure.config.clustering_configs import KMeansConfig

__all__ = ["KMeansAlgorithm"]


class KMeansAlgorithm(ClusteringAlgorithm):
    """KMeans clustering, delegating to sklearn.cluster.KMeans."""

    def fit_predict(self, X: np.ndarray, config: KMeansConfig) -> ClusteringOutput:
        model = KMeans(
            n_clusters=config.n_clusters,
            init=config.init,
            n_init=config.n_init,
            random_state=config.random_state,
            **config.extra_params,
        )
        labels = model.fit_predict(X)

        return ClusteringOutput(
            labels=labels,
            model=model,
            inertia=model.inertia_,
            centers=model.cluster_centers_,
        )