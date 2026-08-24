"""
synclair_structure.projection.umap_projection
---------------------------------------------------

UMAP projection algorithm. Migrated from the legacy run_umap function;
mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import numpy as np
import umap

from synclair_structure.config.projection_configs import UMAPConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["UMAPProjection"]


class UMAPProjection(ProjectionAlgorithm):
    """UMAP projection, delegating to umap.UMAP."""

    def fit_transform(self, X: np.ndarray, config: UMAPConfig) -> ProjectionOutput:
        model = umap.UMAP(
            n_components=config.n_components,
            n_neighbors=config.n_neighbors,
            min_dist=config.min_dist,
            metric=config.metric,
            random_state=config.random_state,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(embedding=embedding, model=model)
    