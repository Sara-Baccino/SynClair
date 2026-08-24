"""
synclair_structure.projection.tsne
--------------------------------------

t-SNE projection algorithm. Migrated from the legacy run_tsne function;
mathematical behaviour and defaults are unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.manifold import TSNE

from synclair_structure.config.projection_configs import TSNEConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["TSNEProjection"]


class TSNEProjection(ProjectionAlgorithm):
    """t-SNE projection, delegating to sklearn.manifold.TSNE."""

    def fit_transform(self, X: np.ndarray, config: TSNEConfig) -> ProjectionOutput:
        model = TSNE(
            n_components=config.n_components,
            perplexity=config.perplexity,
            learning_rate=config.learning_rate,
            init=config.init,
            random_state=config.random_state,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(embedding=embedding, model=model)