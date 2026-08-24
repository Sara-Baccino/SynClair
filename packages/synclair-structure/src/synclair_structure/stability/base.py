"""
synclair_structure.stability.base
--------------------------------------

Abstract contract for cluster-stability evaluators. A StabilityEvaluator
measures how robust a clustering assignment is to data perturbation
(e.g. bootstrap resampling), receiving the clustering algorithm to
evaluate as a callable collaborator (cluster_fn), not implementing one
itself -- mirroring how the legacy evaluate_cluster_stability_bootstrap
received cluster_func as a parameter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["StabilityOutput", "StabilityEvaluator"]


class StabilityOutput(BaseModel):
    """Uniform result shape for every stability evaluator.

    Fields mirror exactly what evaluate_cluster_stability_bootstrap
    returned: mean/std ARI across iterations, the raw per-iteration ARI
    scores, and the per-cluster Jaccard stability averaged across
    iterations (via optimal cluster matching).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    mean_ari: float
    std_ari: float
    all_ari_scores: list[float] = Field(default_factory=list)
    per_cluster_jaccard_stability: np.ndarray


class StabilityEvaluator(ABC):
    """Abstract base class for a cluster-stability evaluator.

    Implementations receive a raw numeric matrix (see the
    StructureModule boundary decision) and a callable `cluster_fn` that
    runs the clustering algorithm being evaluated on a given matrix,
    returning its label assignment.
    """

    @abstractmethod
    def evaluate(
        self,
        X: np.ndarray,
        cluster_fn: Callable[[np.ndarray], np.ndarray],
        config: BaseModel,
    ) -> StabilityOutput:
        """Evaluate the stability of `cluster_fn`'s assignments on `X`.

        :param X: numeric feature matrix, shape (n_samples, n_features).
        :param cluster_fn: callable that takes a numeric matrix and
            returns cluster labels, e.g. a bound clustering algorithm.
        :param config: Pydantic config with this evaluator's parameters.
        :return: StabilityOutput with the evaluator's stability metrics.
        """
        raise NotImplementedError