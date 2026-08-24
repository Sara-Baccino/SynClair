"""
synclair_structure.config.projection_configs
-------------------------------------------------

Pydantic configuration objects for every projection/dimensionality-
reduction algorithm. Mirrors the legacy functions' `cfg.get(...)`
defaults exactly, including PCAConfig's n_components/target_variance
fallback logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = [
    "PCAConfig",
    "UMAPConfig",
    "TSNEConfig",
    "SVDConfig",
    "KernelPCAConfig",
    "PaCMAPConfig",
]


class PCAConfig(BaseModel):
    """Configuration for PCAProjection. Mirrors run_pca's legacy defaults.

    Preserves the legacy fallback: n_components (if given) wins;
    otherwise target_variance (if given) is used as n_components
    (sklearn interprets a float in (0, 1) as a target explained-variance
    ratio); otherwise the default is 2.
    """

    model_config = ConfigDict(extra="forbid")

    n_components: int | float | None = None
    target_variance: float | None = None
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _resolve_n_components(self) -> "PCAConfig":
        if self.n_components is None:
            self.n_components = self.target_variance if self.target_variance is not None else 2
        return self


class UMAPConfig(BaseModel):
    """Configuration for UMAPProjection. Mirrors run_umap's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 2
    n_neighbors: int = 15
    min_dist: float = 0.1
    metric: str = "euclidean"
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class TSNEConfig(BaseModel):
    """Configuration for TSNEProjection. Mirrors run_tsne's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 2
    perplexity: float = 30.0
    learning_rate: str | float = "auto"
    init: str = "pca"
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class SVDConfig(BaseModel):
    """Configuration for TruncatedSVDProjection. Mirrors run_svd's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 2
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)


class KernelPCAConfig(BaseModel):
    """Configuration for KernelPCAProjection. Mirrors run_kernel_pca's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 2
    kernel: Literal["linear", "poly", "rbf", "sigmoid", "cosine", "precomputed"] = "rbf"
    gamma: float | None = None
    random_state: int | None = 42
    fit_inverse_transform: bool = False
    extra_params: dict[str, Any] = Field(default_factory=dict)


class PaCMAPConfig(BaseModel):
    """Configuration for PaCMAPProjection. Mirrors run_pacmap's legacy defaults."""

    model_config = ConfigDict(extra="forbid")

    n_components: int = 2
    n_neighbors: int = 10
    MN_ratio: float = 0.5
    FP_ratio: float = 2.0
    random_state: int | None = 42
    extra_params: dict[str, Any] = Field(default_factory=dict)