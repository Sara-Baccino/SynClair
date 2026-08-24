"""
synclair_structure.explainability.base
--------------------------------------------

Abstract contracts for the three explainability concerns: feature
importance ranking, model-level explanations (e.g. SHAP), and
descriptive cluster profiling. Kept as three distinct ABCs since their
output shapes and purposes are genuinely different, mirroring how the
legacy functions already served different purposes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import polars as pl
from pydantic import BaseModel, ConfigDict

__all__ = [
    "FeatureImportanceExplainer",
    "ShapOutput",
    "ModelExplainer",
    "ClusterProfileOutput",
    "ClusterProfiler",
]


class FeatureImportanceExplainer(ABC):
    """Ranks features by their importance for distinguishing clusters.

    E.g. Random Forest feature importance trained on cluster labels.
    """

    @abstractmethod
    def compute(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        feature_names: list[str] | None,
        config: BaseModel,
    ) -> pl.DataFrame:
        """:return: a DataFrame with 'feature' and 'importance' columns, sorted descending."""
        raise NotImplementedError


class ShapOutput(BaseModel):
    """Uniform result shape for model-explainer outputs (e.g. SHAP).

    Mirrors exactly what compute_shap_values returned: the fitted
    explainer, the raw SHAP values, the (noise-masked) data they were
    computed on, and the feature names.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    explainer: Any
    shap_values: Any
    X_data: np.ndarray
    feature_names: list[str]


class ModelExplainer(ABC):
    """Produces model-level explanations (e.g. SHAP values) for a
    surrogate model trained on cluster labels.
    """

    @abstractmethod
    def compute(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        feature_names: list[str] | None,
        config: BaseModel,
    ) -> ShapOutput:
        """:return: ShapOutput with the fitted explainer and computed values."""
        raise NotImplementedError


class ClusterProfileOutput(BaseModel):
    """Uniform result shape for descriptive cluster profiling.

    Mirrors exactly what compute_cluster_profiles returned: per-cluster
    means, medians, and z-scores relative to the global population.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cluster_means: pl.DataFrame
    cluster_medians: pl.DataFrame
    cluster_z_scores: pl.DataFrame


class ClusterProfiler(ABC):
    """Computes descriptive statistics per cluster (mean, median, z-score)."""

    @abstractmethod
    def compute(
        self,
        df: pl.DataFrame,
        labels: np.ndarray,
        features: list[str] | None,
    ) -> ClusterProfileOutput:
        """:return: ClusterProfileOutput with per-cluster descriptive statistics."""
        raise NotImplementedError