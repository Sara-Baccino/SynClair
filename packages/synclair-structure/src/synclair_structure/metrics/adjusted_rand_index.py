"""
synclair_structure.metrics.adjusted_rand_index
-----------------------------------------------------

Adjusted Rand Index (ARI) partition-comparison metric. Migrated from
the legacy calculate_adjusted_rand_index function; mathematical
behaviour is unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import adjusted_rand_score

from synclair_structure.metrics.base import PartitionComparisonMetric

__all__ = ["AdjustedRandIndexMetric"]


class AdjustedRandIndexMetric(PartitionComparisonMetric):
    """Adjusted Rand Index (ARI) between two label partitions."""

    def compute(self, labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
        return float(adjusted_rand_score(labels_true, labels_pred))