"""
synclair_structure.config.stability_config
-----------------------------------------------

Pydantic configuration for BootstrapStabilityEvaluator. Mirrors
evaluate_cluster_stability_bootstrap's legacy defaults exactly.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["BootstrapStabilityConfig"]


class BootstrapStabilityConfig(BaseModel):
    """Configuration for BootstrapStabilityEvaluator."""

    model_config = ConfigDict(extra="forbid")

    n_iterations: int = 50
    sample_fraction: float = 0.8
    seed: int = 42