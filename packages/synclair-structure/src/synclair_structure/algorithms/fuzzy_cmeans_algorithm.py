"""
synclair_structure.algorithms.fuzzy_cmeans_algorithm
-----------------------------------------------------------

Fuzzy C-Means clustering algorithm. Migrated from the legacy
run_fuzzy_cmeans function; mathematical behaviour and defaults are
unchanged. The pandas-DataFrame branch from the legacy code is dropped
since StructureModule guarantees a raw np.ndarray at this boundary (see
migration decision #1); the underlying transpose/argmax math is
otherwise identical.
"""

from __future__ import annotations

import numpy as np
import skfuzzy as fuzzy

from synclair_structure.algorithms.base import ClusteringAlgorithm, ClusteringOutput
from synclair_structure.config.clustering_configs import FuzzyCMeansConfig

__all__ = ["FuzzyCMeansAlgorithm"]


class FuzzyCMeansAlgorithm(ClusteringAlgorithm):
    """Fuzzy C-Means clustering, delegating to skfuzzy.cluster.cmeans."""

    def fit_predict(self, X: np.ndarray, config: FuzzyCMeansConfig) -> ClusteringOutput:
        X_data = X.T

        cntr, u, u0, d, jm, p, fpc = fuzzy.cluster.cmeans(
            X_data,
            c=config.n_clusters,
            m=config.m,
            error=config.error,
            maxiter=config.maxiter,
            init=config.init,
            seed=config.random_state,
            **config.extra_params,
        )

        labels = np.argmax(u, axis=0)

        return ClusteringOutput(
            labels=labels,
            model=None,
            membership_matrix=u.T,
            centers=cntr,
            fpc=float(fpc),
        )