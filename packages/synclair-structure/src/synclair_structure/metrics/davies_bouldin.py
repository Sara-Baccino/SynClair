"""
synclair_structure.metrics.davies_bouldin
------------------------------------------------

Davies-Bouldin index clustering metric. Migrated from the legacy
calculate_davies_bouldin function; mathematical behaviour is unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import davies_bouldin_score

from synclair_structure.metrics.base import ClusteringMetric

__all__ = ["DaviesBouldinMetric"]


class DaviesBouldinMetric(ClusteringMetric):
    """Davies-Bouldin index (lower values indicate better cluster separation)."""

    def compute(self, X: np.ndarray, labels: np.ndarray) -> float:
        unique_labels = np.unique(labels[labels != -1])
        if len(unique_labels) < 2:
            return float(np.nan)

        mask = labels != -1 if -1 in labels else np.ones(len(labels), dtype=bool)
        return float(davies_bouldin_score(X[mask], labels[mask]))