"""
synclair_structure.explainability.shap_explainer
----------------------------------------------------

SHAP (SHapley Additive exPlanations) model explainer, based on
TreeExplainer over a Random Forest surrogate trained on cluster labels.
Migrated from the legacy compute_shap_values function; mathematical
behaviour is unchanged. Same np.ndarray boundary simplification as
RandomForestImportanceExplainer (migration decision #1).
"""

from __future__ import annotations

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier

from synclair_structure.config.explainability_configs import ShapConfig
from synclair_structure.explainability.base import ModelExplainer, ShapOutput

__all__ = ["ShapExplainer"]


class ShapExplainer(ModelExplainer):
    """SHAP values via TreeExplainer over a Random Forest surrogate model."""

    def compute(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        feature_names: list[str] | None,
        config: ShapConfig,
    ) -> ShapOutput:
        mask = labels != -1 if -1 in labels else np.ones(len(labels), dtype=bool)

        resolved_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        clf = RandomForestClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            random_state=config.random_state,
            **config.extra_params,
        )
        clf.fit(X[mask], labels[mask])

        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X[mask])

        return ShapOutput(
            explainer=explainer,
            shap_values=shap_values,
            X_data=X[mask],
            feature_names=resolved_names,
        )