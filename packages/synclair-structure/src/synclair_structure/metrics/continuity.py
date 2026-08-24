"""
synclair_structure.metrics.continuity
------------------------------------------

Continuity projection-quality metric: complementary to trustworthiness,
measuring whether points that were neighbors in the projected space
were also neighbors in the original space. Migrated from the legacy
calculate_continuity function; mathematical behaviour is unchanged
(same trustworthiness() call with arguments swapped).
"""

from __future__ import annotations

import numpy as np
from sklearn.manifold import trustworthiness

from synclair_structure.metrics.base import ProjectionQualityMetric

__all__ = ["ContinuityMetric"]


class ContinuityMetric(ProjectionQualityMetric):
    """Continuity: complementary to Trustworthiness, with X_low/X_high swapped."""

    def __init__(self, n_neighbors: int = 5) -> None:
        self.n_neighbors = n_neighbors

    def compute(self, X_high: np.ndarray, X_low: np.ndarray) -> float:
        return float(trustworthiness(X_low, X_high, n_neighbors=self.n_neighbors))