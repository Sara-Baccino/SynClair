"""
synclair_structure.explainability.rf_importance
--------------------------------------------------------

Random Forest feature-importance explainer. Migrated from the legacy
compute_rf_feature_importance function; mathematical behaviour is
unchanged. The pandas-DataFrame column-name branch from the legacy code
is dropped since StructureModule guarantees a raw np.ndarray at this
boundary (migration decision #1); the feature_{i} fallback when no
names are supplied is preserved identically.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestClassifier

from synclair_structure.config.explainability_configs import RFImportanceConfig
from synclair_structure.explainability.base import FeatureImportanceExplainer

__all__ = ["RandomForestImportanceExplainer"]


class RandomForestImportanceExplainer(FeatureImportanceExplainer):
    """Feature importance via a Random Forest classifier trained on cluster labels."""

    def compute(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        feature_names: list[str] | None,
        config: RFImportanceConfig,
    ) -> pl.DataFrame:
        mask = labels != -1 if -1 in labels else np.ones(len(labels), dtype=bool)

        resolved_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        clf = RandomForestClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            random_state=config.random_state,
            **config.extra_params,
        )
        clf.fit(X[mask], labels[mask])

        return pl.DataFrame(
            {"feature": resolved_names, "importance": clf.feature_importances_}
        ).sort("importance", descending=True)