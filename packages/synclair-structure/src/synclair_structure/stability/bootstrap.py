"""
synclair_structure.stability.bootstrap
--------------------------------------------

Bootstrap-resampling cluster-stability evaluator. Migrated from the
legacy evaluate_cluster_stability_bootstrap function; mathematical
behaviour is unchanged. Composes AdjustedRandIndexMetric and
JaccardPartitionSimilarityMetric rather than duplicating their logic.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.optimize import linear_sum_assignment

from synclair_structure.config.stability_config import BootstrapStabilityConfig
from synclair_structure.metrics.adjusted_rand_index import AdjustedRandIndexMetric
from synclair_structure.metrics.jaccard_partition_similarity import JaccardPartitionSimilarityMetric
from synclair_structure.stability.base import StabilityEvaluator, StabilityOutput

__all__ = ["BootstrapStabilityEvaluator"]


class BootstrapStabilityEvaluator(StabilityEvaluator):
    """Evaluates cluster stability via bootstrap resampling.

    Computes the mean/std Adjusted Rand Index across resampled
    iterations, plus per-cluster Jaccard stability via optimal cluster
    matching between the reference and each resampled partition.
    """

    def __init__(
        self,
        adjusted_rand_index_metric: AdjustedRandIndexMetric | None = None,
        jaccard_metric: JaccardPartitionSimilarityMetric | None = None,
    ) -> None:
        self._ari_metric = adjusted_rand_index_metric or AdjustedRandIndexMetric()
        self._jaccard_metric = jaccard_metric or JaccardPartitionSimilarityMetric()

    def evaluate(
        self,
        X: np.ndarray,
        cluster_fn: Callable[[np.ndarray], np.ndarray],
        config: BootstrapStabilityConfig,
    ) -> StabilityOutput:
        n_samples = len(X)
        subsample_size = int(n_samples * config.sample_fraction)

        # Reference clustering on the full dataset
        ref_labels = cluster_fn(X)

        ari_scores: list[float] = []
        jaccard_per_iteration: list[np.ndarray] = []

        rng = np.random.default_rng(config.seed)

        for _ in range(config.n_iterations):
            indices = rng.choice(n_samples, size=subsample_size, replace=True)
            sub_X = X[indices]

            # Clustering on the subsample
            sub_labels = cluster_fn(sub_X)

            # Reference labels corresponding to the same indices
            ref_sub_labels = ref_labels[indices]

            # ARI of the resampling
            ari = self._ari_metric.compute(ref_sub_labels, sub_labels)
            ari_scores.append(ari)

            # Jaccard similarity, optimally matched to align clusters
            j_mat = self._jaccard_metric.compute(ref_sub_labels, sub_labels)
            if j_mat.size > 0:
                row_ind, col_ind = linear_sum_assignment(-j_mat)
                jaccard_per_iteration.append(j_mat[row_ind, col_ind])

        avg_jaccard_per_cluster = (
            np.mean(jaccard_per_iteration, axis=0) if jaccard_per_iteration else np.array([])
        )

        return StabilityOutput(
            mean_ari=float(np.mean(ari_scores)),
            std_ari=float(np.std(ari_scores)),
            all_ari_scores=ari_scores,
            per_cluster_jaccard_stability=avg_jaccard_per_cluster,
        )