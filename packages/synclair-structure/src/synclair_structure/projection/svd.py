"""
synclair_structure.projection.svd
--------------------------------------

TruncatedSVD projection algorithm. Migrated from the legacy run_svd
function; mathematical behaviour and defaults are unchanged. Note: the
legacy function did not compute cumulative_variance for SVD (unlike
PCA), so that field is left unset here too.
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import TruncatedSVD

from synclair_structure.config.projection_configs import SVDConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["TruncatedSVDProjection"]


class TruncatedSVDProjection(ProjectionAlgorithm):
    """TruncatedSVD projection, delegating to sklearn.decomposition.TruncatedSVD."""

    def fit_transform(self, X: np.ndarray, config: SVDConfig) -> ProjectionOutput:
        model = TruncatedSVD(
            n_components=config.n_components,
            random_state=config.random_state,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(
            embedding=embedding,
            model=model,
            explained_variance_ratio=model.explained_variance_ratio_,
        )