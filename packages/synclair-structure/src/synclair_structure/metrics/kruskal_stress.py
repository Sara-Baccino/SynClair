"""
synclair_structure.metrics.kruskal_stress
------------------------------------------------

Kruskal Stress-1 projection-quality metric, measuring distance
distortion between the high- and low-dimensional spaces. Migrated from
the legacy calculate_kruskal_stress function; mathematical behaviour is
unchanged.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist

from synclair_structure.metrics.base import ProjectionQualityMetric

__all__ = ["KruskalStressMetric"]


class KruskalStressMetric(ProjectionQualityMetric):
    """Kruskal Stress-1: distortion of pairwise distances between spaces."""

    def compute(self, X_high: np.ndarray, X_low: np.ndarray) -> float:
        d_high = pdist(X_high, metric="euclidean")
        d_low = pdist(X_low, metric="euclidean")

        numerator = np.sum((d_high - d_low) ** 2)
        denominator = np.sum(d_low ** 2)

        if denominator == 0:
            return 0.0
        return float(np.sqrt(numerator / denominator))