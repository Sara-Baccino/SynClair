"""
synclair_structure.projection.pacmap_projection
--------------------------------------------------------

PaCMAP projection algorithm. Migrated from the legacy run_pacmap
function; mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import numpy as np
import pacmap

from synclair_structure.config.projection_configs import PaCMAPConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["PaCMAPProjection"]


class PaCMAPProjection(ProjectionAlgorithm):
    """PaCMAP projection, delegating to pacmap.PaCMAP."""

    def fit_transform(self, X: np.ndarray, config: PaCMAPConfig) -> ProjectionOutput:
        model = pacmap.PaCMAP(
            n_components=config.n_components,
            n_neighbors=config.n_neighbors,
            MN_ratio=config.MN_ratio,
            FP_ratio=config.FP_ratio,
            random_state=config.random_state,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(embedding=embedding, model=model)