from __future__ import annotations
from pydantic import BaseModel, ConfigDict

from synclair_matching.config.causal_estimation_config import CausalEstimationConfig
from synclair_matching.config.constraints_config import ConstraintsConfig
from synclair_matching.config.covariates_config import CovariatesConfig
from synclair_matching.config.diagnostics_config import DiagnosticsConfig
from synclair_matching.config.distance_config import DistanceConfig
from synclair_matching.config.population_config import PopulationConfig
from synclair_matching.config.preprocessing_config import MatchingPreprocessingConfig
from synclair_matching.config.representation_config import RepresentationConfig
from synclair_matching.config.strategy_config import StrategyConfig

__all__ = ["MatchingModuleConfig"]


class MatchingModuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    population: PopulationConfig
    covariates: CovariatesConfig
    preprocessing: MatchingPreprocessingConfig = MatchingPreprocessingConfig()
    representation: RepresentationConfig = RepresentationConfig()
    constraints: ConstraintsConfig = ConstraintsConfig()
    distance: DistanceConfig = DistanceConfig()
    strategy: StrategyConfig = StrategyConfig()
    diagnostics: DiagnosticsConfig = DiagnosticsConfig()
    causal_estimation: CausalEstimationConfig | None = None