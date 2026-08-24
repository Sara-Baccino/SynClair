"""
synclair_structure.metrics.jaccard_partition_similarity
--------------------------------------------------------------

Jaccard partition-similarity-matrix metric. Migrated from the legacy
_jaccard_similarity_matrix private helper (previously embedded in
stability.py); mathematical behaviour is unchanged. Extracted as a
standalone, reusable metric rather than a hidden implementation detail,
so BootstrapStabilityEvaluator uses it by composition.
"""

from __future__ import annotations

import numpy as np

from synclair_structure.metrics.base import PartitionSimilarityMatrixMetric

__all__ = ["JaccardPartitionSimilarityMetric"]


class JaccardPartitionSimilarityMetric(PartitionSimilarityMatrixMetric):
    """Pairwise Jaccard similarity matrix between the clusters of two partitions.

    Noise points (label == -1) are excluded from both partitions before
    comparison, matching the legacy helper's behaviour.
    """

    def compute(self, labels1: np.ndarray, labels2: np.ndarray) -> np.ndarray:
        u1, u2 = np.unique(labels1[labels1 != -1]), np.unique(labels2[labels2 != -1])
        matrix = np.zeros((len(u1), len(u2)))

        for i, c1 in enumerate(u1):
            mask1 = labels1 == c1
            for j, c2 in enumerate(u2):
                mask2 = labels2 == c2
                intersection = np.sum(mask1 & mask2)
                union = np.sum(mask1 | mask2)
                matrix[i, j] = intersection / union if union > 0 else 0.0

        return matrix