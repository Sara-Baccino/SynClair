"""
synclair_structure.metrics.silhouette
------------------------------------------

Silhouette Score clustering metric. Migrated from the legacy
calculate_silhouette function; mathematical behaviour is unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import silhouette_score

from synclair_structure.metrics.base import ClusteringMetric

__all__ = ["SilhouetteMetric"]


class SilhouetteMetric(ClusteringMetric):
    """Silhouette Score. Returns np.nan if there is only one cluster (or only noise)."""

    def __init__(self, sample_size: int | None = None) -> None:
        self.sample_size = sample_size

    def compute(self, X: np.ndarray, labels: np.ndarray) -> float:
        unique_labels = np.unique(labels[labels != -1])
        if len(unique_labels) < 2:
            return float(np.nan)

        mask = labels != -1 if -1 in labels else np.ones(len(labels), dtype=bool)
        if np.sum(mask) < 2:
            return float(np.nan)

        return float(silhouette_score(X[mask], labels[mask], sample_size=self.sample_size))