"""
synclair_structure.metrics.trustworthiness
---------------------------------------------------

Trustworthiness projection-quality metric: how well local neighborhood
structure is preserved from the original to the projected space.
Migrated from the legacy calculate_trustworthiness function;
mathematical behaviour is unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.manifold import trustworthiness

from synclair_structure.metrics.base import ProjectionQualityMetric

__all__ = ["TrustworthinessMetric"]


class TrustworthinessMetric(ProjectionQualityMetric):
    """Trustworthiness: how well local neighbor structure is preserved
    from the original space to the projected space.
    """

    def __init__(self, n_neighbors: int = 5) -> None:
        self.n_neighbors = n_neighbors

    def compute(self, X_high: np.ndarray, X_low: np.ndarray) -> float:
        return float(trustworthiness(X_high, X_low, n_neighbors=self.n_neighbors))