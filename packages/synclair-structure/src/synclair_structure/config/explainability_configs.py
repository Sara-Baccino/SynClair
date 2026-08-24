"""
synclair_structure.config.explainability_configs
-----------------------------------------------------

Pydantic configuration objects for the explainability family. Mirrors
the legacy functions' cfg.get(...) defaults exactly, including the
differing max_depth default between RF feature importance (6) and SHAP
(5) in the original code.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["RFImportanceConfig", "ShapConfig"]


class RFImportanceConfig(BaseModel):
    """Configuration for RandomForestImportanceExplainer.

    Mirrors compute_rf_feature_importance's legacy defaults.
    """

    model_config = ConfigDict(extra="forbid")

    n_estimators: int = 100
    max_depth: int = 6
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class ShapConfig(BaseModel):
    """Configuration for ShapExplainer.

    Mirrors compute_shap_values's legacy defaults (note max_depth=5,
    differing from RFImportanceConfig's 6, exactly as in the legacy code).
    """

    model_config = ConfigDict(extra="forbid")

    n_estimators: int = 100
    max_depth: int = 5
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)