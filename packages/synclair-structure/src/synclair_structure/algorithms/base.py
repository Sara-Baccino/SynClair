"""
synclair_structure.algorithms.base
--------------------------------------

Abstract contract for every clustering algorithm in synclair-structure.
Concrete algorithms (HDBSCAN, KMeans, Agglomerative, GMM, Fuzzy C-Means)
implement fit_predict(X, config) -> ClusteringOutput, so StructureModule
can run any of them interchangeably.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ClusteringOutput", "ClusteringAlgorithm"]


class ClusteringOutput(BaseModel):
    """Uniform result shape for every clustering algorithm.

    Fields mirror exactly what the legacy functions returned, kept
    optional since not every algorithm produces every field (e.g. only
    KMeans/Fuzzy C-Means produce `centers`; only GMM produces `bic`/`aic`).
    No field is synthesized for an algorithm that didn't natively produce
    it, preserving the legacy public behaviour as-is.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    labels: np.ndarray
    model: Any = Field(description="The fitted underlying model/estimator instance.")

    probabilities: np.ndarray | None = None
    """Soft-assignment probabilities (HDBSCAN, GMM)."""
    centers: np.ndarray | None = None
    """Cluster centers (KMeans, Fuzzy C-Means)."""
    inertia: float | None = None
    """Sum of squared intra-cluster distances (KMeans)."""
    membership_matrix: np.ndarray | None = None
    """(n_samples, n_clusters) fuzzy membership matrix (Fuzzy C-Means)."""
    fpc: float | None = None
    """Fuzzy Partition Coefficient (Fuzzy C-Means)."""
    bic: float | None = None
    """Bayesian Information Criterion (GMM)."""
    aic: float | None = None
    """Akaike Information Criterion (GMM)."""


class ClusteringAlgorithm(ABC):
    """Abstract base class for a clustering algorithm.

    Implementations receive a raw numeric matrix (see the migration
    decision to normalize DataFrame/DataConfig extraction at the
    StructureModule boundary, not inside individual algorithms) and a
    Pydantic config object with the algorithm's own parameters.
    """

    @abstractmethod
    def fit_predict(self, X: np.ndarray, config: BaseModel) -> ClusteringOutput:
        """Fit the algorithm on `X` and return cluster assignments plus
        any algorithm-specific byproducts (centers, probabilities, ...).

        :param X: numeric feature matrix, shape (n_samples, n_features).
        :param config: Pydantic config with this algorithm's parameters.
        :return: ClusteringOutput with at least `labels` and `model` set.
        """
        raise NotImplementedError