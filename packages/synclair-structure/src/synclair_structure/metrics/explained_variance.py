"""
synclair_structure.metrics.explained_variance
-----------------------------------------------------

Explained-variance-ratio extraction, model-diagnostic metric. Migrated
from the legacy calculate_explained_variance_ratio function;
mathematical behaviour is unchanged.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from synclair_structure.metrics.base import ModelDiagnosticMetric

__all__ = ["ExplainedVarianceMetric"]


class ExplainedVarianceMetric(ModelDiagnosticMetric):
    """Extracts per-component and cumulative explained variance ratio.

    Accepts either a fitted model exposing `explained_variance_ratio_`
    (e.g. PCA, TruncatedSVD) or a raw array of ratios.
    """

    def compute(self, model_or_values: Any) -> dict[str, Any]:
        if hasattr(model_or_values, "explained_variance_ratio_"):
            ratios = model_or_values.explained_variance_ratio_
        else:
            ratios = np.asarray(model_or_values)

        return {
            "ratio_per_component": ratios,
            "cumulative_ratio": np.cumsum(ratios),
            "total_explained": float(np.sum(ratios)),
        }