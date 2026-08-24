"""
synclair_structure.projection.kernel_pca
------------------------------------------------

Kernel PCA projection algorithm. Migrated from the legacy
run_kernel_pca function; mathematical behaviour and defaults are
unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import KernelPCA

from synclair_structure.config.projection_configs import KernelPCAConfig
from synclair_structure.projection.base import ProjectionAlgorithm, ProjectionOutput

__all__ = ["KernelPCAProjection"]


class KernelPCAProjection(ProjectionAlgorithm):
    """Kernel PCA projection, delegating to sklearn.decomposition.KernelPCA."""

    def fit_transform(self, X: np.ndarray, config: KernelPCAConfig) -> ProjectionOutput:
        model = KernelPCA(
            n_components=config.n_components,
            kernel=config.kernel,
            gamma=config.gamma,
            random_state=config.random_state,
            fit_inverse_transform=config.fit_inverse_transform,
            **config.extra_params,
        )
        embedding = model.fit_transform(X)

        return ProjectionOutput(embedding=embedding, model=model)