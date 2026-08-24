"""
synclair_structure.algorithms.gmm_algorithm
-------------------------------------------------

Gaussian Mixture Model clustering algorithm. Migrated from the legacy
run_gmm function; mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.mixture import GaussianMixture

from synclair_structure.algorithms.base import ClusteringAlgorithm, ClusteringOutput
from synclair_structure.config.clustering_configs import GMMConfig

__all__ = ["GaussianMixtureAlgorithm"]


class GaussianMixtureAlgorithm(ClusteringAlgorithm):
    """Gaussian Mixture Model clustering, delegating to sklearn.mixture.GaussianMixture."""

    def fit_predict(self, X: np.ndarray, config: GMMConfig) -> ClusteringOutput:
        model = GaussianMixture(
            n_components=config.n_components,
            covariance_type=config.covariance_type,
            random_state=config.random_state,
            **config.extra_params,
        )
        labels = model.fit_predict(X)
        probabilities = model.predict_proba(X)

        return ClusteringOutput(
            labels=labels,
            model=model,
            probabilities=probabilities,
            bic=model.bic(X),
            aic=model.aic(X),
        )