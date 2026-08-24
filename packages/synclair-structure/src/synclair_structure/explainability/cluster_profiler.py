"""
synclair_structure.explainability.cluster_profiler
--------------------------------------------------------

Descriptive cluster profiler: per-cluster mean, median, and z-score
relative to the global population. Migrated from the legacy
compute_cluster_profiles function; mathematical behaviour is unchanged.

Adaptation note: the legacy pandas version used cluster as an implicit
groupby index; since Polars has no persistent index, `cluster` is kept
as an explicit column in each output DataFrame instead. The numeric
content and meaning of every row/column is otherwise identical.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from synclair_structure.explainability.base import ClusterProfiler, ClusterProfileOutput

__all__ = ["DescriptiveClusterProfiler"]

_ZERO_STD_REPLACEMENT = 1e-6


class DescriptiveClusterProfiler(ClusterProfiler):
    """Per-cluster mean, median, and z-score relative to the global population."""

    def compute(
        self,
        df: pl.DataFrame,
        labels: np.ndarray,
        features: list[str] | None,
    ) -> ClusterProfileOutput:
        df_work = df.select(features) if features else df
        df_work = df_work.with_columns(pl.Series("cluster", labels))

        # Exclude noise (-1) from the profile, as in the legacy code.
        df_active = df_work.filter(pl.col("cluster") != -1)
        feature_cols = [c for c in df_active.columns if c != "cluster"]

        means = (
            df_active.group_by("cluster", maintain_order=True)
            .agg([pl.col(c).mean().alias(c) for c in feature_cols])
            .sort("cluster")
        )
        medians = (
            df_active.group_by("cluster", maintain_order=True)
            .agg([pl.col(c).median().alias(c) for c in feature_cols])
            .sort("cluster")
        )

        global_mean_row = df_active.select(feature_cols).mean().row(0)
        global_std_row = df_active.select(feature_cols).std().row(0)
        # Z-score of the cluster relative to the global population.
        global_std_row = tuple(
            _ZERO_STD_REPLACEMENT if std == 0 else std for std in global_std_row
        )

        z_score_expressions = [
            ((pl.col(c) - global_mean_row[i]) / global_std_row[i]).alias(c)
            for i, c in enumerate(feature_cols)
        ]
        z_scores = means.select(["cluster", *feature_cols]).with_columns(z_score_expressions)

        return ClusterProfileOutput(
            cluster_means=means,
            cluster_medians=medians,
            cluster_z_scores=z_scores,
        )