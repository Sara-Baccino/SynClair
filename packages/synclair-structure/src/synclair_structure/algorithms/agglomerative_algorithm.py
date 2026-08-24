"""
synclair_structure.algorithms.agglomerative_algorithm
-----------------------------------------------------------

Hierarchical Agglomerative Clustering algorithm. Migrated from the
legacy run_agglomerative function; mathematical behaviour and defaults
are unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from synclair_structure.algorithms.base import ClusteringAlgorithm, ClusteringOutput
from synclair_structure.config.clustering_configs import AgglomerativeConfig

__all__ = ["AgglomerativeAlgorithm"]


class AgglomerativeAlgorithm(ClusteringAlgorithm):
    """Hierarchical Agglomerative Clustering, delegating to sklearn."""

    def fit_predict(self, X: np.ndarray, config: AgglomerativeConfig) -> ClusteringOutput:
        model = AgglomerativeClustering(
            n_clusters=config.n_clusters,
            metric=config.metric,
            linkage=config.linkage,
            **config.extra_params,
        )
        labels = model.fit_predict(X)

        return ClusteringOutput(labels=labels, model=model)