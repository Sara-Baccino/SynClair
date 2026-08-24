"""
synclair_structure.projection.base
--------------------------------------

Abstract contract for every dimensionality-reduction/projection
algorithm in synclair-structure. Concrete algorithms (PCA, UMAP, t-SNE,
TruncatedSVD, Kernel PCA, PaCMAP) implement
fit_transform(X, config) -> ProjectionOutput, so StructureModule can run
any of them interchangeably ahead of clustering.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ProjectionOutput", "ProjectionAlgorithm"]


class ProjectionOutput(BaseModel):
    """Uniform result shape for every projection algorithm.

    Fields mirror exactly what the legacy functions returned: only PCA
    and TruncatedSVD natively produce `explained_variance_ratio`
    (PCA additionally `cumulative_variance`); UMAP, t-SNE, Kernel PCA,
    and PaCMAP return just `embedding`/`model` in the legacy code, and
    still do here.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    embedding: np.ndarray
    model: Any = Field(description="The fitted underlying model/estimator instance.")

    explained_variance_ratio: np.ndarray | None = None
    """Per-component explained variance ratio (PCA, TruncatedSVD)."""
    cumulative_variance: np.ndarray | None = None
    """Cumulative explained variance ratio (PCA only, as in the legacy code)."""


class ProjectionAlgorithm(ABC):
    """Abstract base class for a dimensionality-reduction/projection algorithm.

    Implementations receive a raw numeric matrix (see the
    StructureModule boundary decision, migration plan point 1) and a
    Pydantic config object with the algorithm's own parameters.
    """

    @abstractmethod
    def fit_transform(self, X: np.ndarray, config: BaseModel) -> ProjectionOutput:
        """Fit the algorithm on `X` and return the low-dimensional embedding.

        :param X: numeric feature matrix, shape (n_samples, n_features).
        :param config: Pydantic config with this algorithm's parameters.
        :return: ProjectionOutput with at least `embedding` and `model` set.
        """
        raise NotImplementedError