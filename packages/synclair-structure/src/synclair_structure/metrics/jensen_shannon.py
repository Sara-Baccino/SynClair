"""
synclair_structure.metrics.jensen_shannon
------------------------------------------------

Jensen-Shannon divergence distribution-divergence metric. Migrated from
the legacy calculate_jensen_shannon_divergence function; mathematical
behaviour is unchanged.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import jensenshannon

from synclair_structure.metrics.base import DistributionDivergenceMetric

__all__ = ["JensenShannonDivergenceMetric"]


class JensenShannonDivergenceMetric(DistributionDivergenceMetric):
    """Jensen-Shannon divergence between two probability distributions p and q.

    Returns the divergence (JS^2, a value between 0 and 1 with base 2).
    """

    def __init__(self, base: float | None = 2.0) -> None:
        self.base = base

    def compute(self, p: np.ndarray, q: np.ndarray) -> float:
        p_norm = np.asarray(p, dtype=np.float64) / np.sum(p)
        q_norm = np.asarray(q, dtype=np.float64) / np.sum(q)

        js_distance = jensenshannon(p_norm, q_norm, base=self.base)
        return float(js_distance ** 2)  # jensenshannon() returns the sqrt of the divergence