"""
synclair_structure.projection.pca
--------------------------------------

PCA projection algorithm. Migrated from the legacy run_pca function;
mathematical behaviour and defaults are unchanged. The n_components/
target_variance fallback logic now lives in PCAConfig itself, resolved
before this class ever sees the config.
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from synclair_structure.config.projection_configs import PCAConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["PCAProjection"]


class PCAProjection(ProjectionAlgorithm):
    """PCA projection, delegating to sklearn.decomposition.PCA."""

    def fit_transform(self, X: np.ndarray, config: PCAConfig) -> ProjectionOutput:
        model = PCA(
            n_components=config.n_components,
            random_state=config.random_state,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(
            embedding=embedding,
            model=model,
            explained_variance_ratio=model.explained_variance_ratio_,
            cumulative_variance=np.cumsum(model.explained_variance_ratio_),
        )