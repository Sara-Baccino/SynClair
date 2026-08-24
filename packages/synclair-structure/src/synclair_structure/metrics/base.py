"""
synclair_structure.metrics.base
------------------------------------

Abstract contracts for every metric family in synclair-structure.
Six distinct ABCs instead of one generic Metric, because the legacy
functions' signatures are genuinely incompatible: a clustering metric
takes (X, labels), a partition-comparison metric takes (labels_true,
labels_pred), a projection-quality metric takes (X_high, X_low), etc.
Forcing them into one interface would erase type safety for no benefit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

__all__ = [
    "ClusteringMetric",
    "PartitionComparisonMetric",
    "PartitionSimilarityMatrixMetric",
    "ProjectionQualityMetric",
    "ModelDiagnosticMetric",
    "DistributionDivergenceMetric",
]


class ClusteringMetric(ABC):
    """A metric evaluating a single clustering result against its own data.

    E.g. silhouette score, Davies-Bouldin index, inertia.
    """

    @abstractmethod
    def compute(self, X: np.ndarray, labels: np.ndarray) -> float:
        """:return: the metric value (float, possibly np.nan if undefined)."""
        raise NotImplementedError


class PartitionComparisonMetric(ABC):
    """A metric comparing two label partitions of the same samples.

    E.g. Adjusted Rand Index between a reference and a candidate partition.
    """

    @abstractmethod
    def compute(self, labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
        """:return: the similarity/agreement score between the two partitions."""
        raise NotImplementedError


class PartitionSimilarityMatrixMetric(ABC):
    """A metric producing a pairwise similarity matrix between the
    clusters of two partitions (not a single scalar).

    E.g. Jaccard similarity matrix, used by stability evaluators to
    match clusters across resampled partitions via optimal assignment.
    """

    @abstractmethod
    def compute(self, labels1: np.ndarray, labels2: np.ndarray) -> np.ndarray:
        """:return: matrix of shape (n_clusters_1, n_clusters_2)."""
        raise NotImplementedError


class ProjectionQualityMetric(ABC):
    """A metric evaluating how well a low-dimensional embedding preserves
    structure from the original high-dimensional space.

    E.g. Kruskal stress, trustworthiness, continuity.
    """

    @abstractmethod
    def compute(self, X_high: np.ndarray, X_low: np.ndarray) -> float:
        """:return: the quality/distortion score between the two spaces."""
        raise NotImplementedError


class ModelDiagnosticMetric(ABC):
    """A metric that inspects a fitted model (or its raw outputs) rather
    than comparing data/partitions directly.

    E.g. explained variance ratio extraction from a PCA/SVD model.
    """

    @abstractmethod
    def compute(self, model_or_values: Any) -> dict[str, Any]:
        """:return: a dict of derived diagnostic quantities."""
        raise NotImplementedError


class DistributionDivergenceMetric(ABC):
    """A metric measuring divergence between two probability distributions.

    E.g. Jensen-Shannon divergence.
    """

    @abstractmethod
    def compute(self, p: np.ndarray, q: np.ndarray) -> float:
        """:return: the divergence value between distributions p and q."""
        raise NotImplementedError