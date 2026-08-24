"""
synclair_structure.metrics.inertia
----------------------------------------

Inertia (within-cluster sum of squares) clustering metric. Migrated
from the legacy calculate_inertia function; mathematical behaviour is
unchanged, including the explicit point-by-point accumulation loop.
"""

from __future__ import annotations

import numpy as np

from synclair_structure.metrics.base import ClusteringMetric

__all__ = ["InertiaMetric"]


class InertiaMetric(ClusteringMetric):
    """Inertia: sum of squared intra-cluster distances."""

    def __init__(self, centers: np.ndarray | None = None) -> None:
        self.centers = centers

    def compute(self, X: np.ndarray, labels: np.ndarray) -> float:
        mask = labels != -1 if -1 in labels else np.ones(len(labels), dtype=bool)
        X_clean, labels_clean = X[mask], labels[mask]

        centers = self.centers
        if centers is None:
            unique_labels = np.unique(labels_clean)
            centers = np.array([X_clean[labels_clean == k].mean(axis=0) for k in unique_labels])

        inertia = 0.0
        for i, point in enumerate(X_clean):
            c_idx = labels_clean[i]
            inertia += np.sum((point - centers[c_idx]) ** 2)
        return float(inertia)