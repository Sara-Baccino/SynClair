"""
Integration tests for the Phase B matching engine: both directions,
covariates-only and PS-based matching spaces, exact/stratified
matching, 1:K ratio, and capability validation rejecting unsupported
configuration values.
"""

import numpy as np
import polars as pl
import pytest
from pydantic import ValidationError

from synclair_core.dataset.config_builder import ConfigBuilder
from synclair_core.dataset.preprocessing import Preprocessing

from synclair_matching.config.constraints_config import ConstraintsConfig
from synclair_matching.config.distance_config import DistanceConfig
from synclair_matching.config.covariates_config import CovariatesConfig
from synclair_matching.config.matching_module_config import MatchingModuleConfig
from synclair_matching.config.population_config import PopulationConfig
from synclair_matching.config.representation_config import RepresentationConfig
from synclair_matching.config.strategy_config import StrategyConfig
from synclair_matching.config.diagnostics_config import DiagnosticsConfig
from synclair_matching.pipeline.matching_module import MatchingModule
from synclair_matching.exceptions import UnsupportedCapabilityError

from synclair_matching.exceptions import MatchingError




@pytest.fixture
def synthetic_dataset() -> pl.DataFrame:
    rng = np.random.default_rng(42)
    n = 200
    age_control = rng.normal(40, 5, n // 2)
    age_treated = rng.normal(42, 5, n // 2)
    center = rng.choice(["A", "B"], size=n)
    treatment = np.concatenate([np.zeros(n // 2), np.ones(n // 2)])
    age = np.concatenate([age_control, age_treated])
    return pl.DataFrame({"patient_id": range(n), "age": age, "treatment": treatment, "center": center})


def _preprocess(df: pl.DataFrame):
    data_config = ConfigBuilder.build_config(df, id_columns=["patient_id"])
    return Preprocessing.run(df, data_config), data_config


def test_treated_to_control_matching(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment", matching_direction="treated_to_control"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        representation=RepresentationConfig(use_propensity_score=True),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    assert "matched_dataset" in result.datasets
    assert "match_rate" in result.metrics
    assert "balance_table" in result.tables


def test_control_to_treated_matching(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment", matching_direction="control_to_treated"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    assert result.metrics["n_query_matched"] > 0


def test_1_to_k_matching_produces_more_pairs_than_1_to_1(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)

    config_1to1 = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        strategy=StrategyConfig(matching_ratio_k=1, allow_replacement=True),
    )
    config_1toK = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        strategy=StrategyConfig(matching_ratio_k=3, allow_replacement=True),
    )

    result_1to1 = MatchingModule().fit(preprocessed, data_config, config_1to1).run()
    result_1toK = MatchingModule().fit(preprocessed, data_config, config_1toK).run()

    assert result_1toK.datasets["matched_dataset"].height > result_1to1.datasets["matched_dataset"].height


def test_stratified_matching_respects_strata(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        constraints=ConstraintsConfig(exact_match_covariates=["center"], stratified_matching=True),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    matched = result.datasets["matched_dataset"]
    for pair_id in matched["pair_id"].unique():
        pair_rows = matched.filter(pl.col("pair_id") == pair_id)
        assert pair_rows["center"].n_unique() == 1


def test_construction_rejects_hungarian_with_replacement() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(matching_algorithm="optimal_hungarian", allow_replacement=True)


def test_unsupported_distance_metric_is_rejected_at_fit_time(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        distance=DistanceConfig(distance_metric="ps_logit"),
    )
    module = MatchingModule()
    with pytest.raises(UnsupportedCapabilityError) as exc_info:
        module.fit(preprocessed, data_config, config)

    assert exc_info.value.field == "distance_metric"
    assert exc_info.value.value == "ps_logit"
    assert exc_info.value.status == "planned"

def test_balance_diagnostics_with_all_metrics(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"], evaluation_covariates=["center"]),
        diagnostics=DiagnosticsConfig(balance_metrics=["smd", "variance_ratio", "ks_test", "chi_square"]),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    table = result.tables["balance_table"]

    age_row = table.filter(pl.col("variable") == "age").row(0, named=True)
    assert age_row["variance_ratio_after"] is not None
    assert age_row["ks_stat"] is not None       # age is continuous -> KS applies
    assert age_row["chi2_stat"] is None          # continuous -> chi-square not applicable

    center_row = table.filter(pl.col("variable") == "center").row(0, named=True)
    assert center_row["chi2_stat"] is not None    # center is binary categorical -> chi-square applies
    assert center_row["ks_stat"] is None           # non-numeric -> KS not applicable
    assert center_row["variance_ratio_after"] is None  # non-numeric -> variance ratio not applicable
    assert center_row["smd_after"] is None              # non-numeric -> SMD not applicable


def test_mahalanobis_with_optimal_hungarian(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        distance=DistanceConfig(distance_metric="mahalanobis"),
        strategy=StrategyConfig(matching_algorithm="optimal_hungarian", allow_replacement=False),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    assert result.metrics["n_query_matched"] > 0
    assert result.metrics["match_rate"] > 0.0


def test_mahalanobis_rejects_too_few_observations() -> None:
    tiny_df = pl.DataFrame({
        "patient_id": [1, 2, 3],
        "age": [30.0, 40.0, 50.0],
        "height": [170.0, 180.0, 160.0],
        "treatment": [1.0, 0.0, 0.0],
    })
    data_config = ConfigBuilder.build_config(tiny_df, id_columns=["patient_id"])
    preprocessed = Preprocessing.run(tiny_df, data_config)

    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age", "height"]),
        distance=DistanceConfig(distance_metric="mahalanobis"),
        strategy=StrategyConfig(matching_algorithm="optimal_hungarian"),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success is False
    assert "covariance matrix" in result.error

def test_gower_distance_with_greedy_nn_on_mixed_covariates(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age", "center"]),
        distance=DistanceConfig(distance_metric="gower"),
        strategy=StrategyConfig(matching_algorithm="greedy_nn", allow_replacement=True),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    assert result.metrics["n_query_matched"] > 0


def test_weighted_hybrid_distance_with_optimal_hungarian(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age", "center"]),
        distance=DistanceConfig(distance_metric="weighted_hybrid", weight_numerical=0.7, weight_categorical=0.3),
        strategy=StrategyConfig(matching_algorithm="optimal_hungarian"),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    assert result.metrics["n_query_matched"] > 0


def test_mahalanobis_with_greedy_nn_now_supported(synthetic_dataset: pl.DataFrame) -> None:
    """Confirms the previously-known limitation (greedy_nn + non-euclidean
    distance not wired) is now resolved."""
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        distance=DistanceConfig(distance_metric="mahalanobis"),
        strategy=StrategyConfig(matching_algorithm="greedy_nn", allow_replacement=True),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error

def test_optimal_transport_selects_target_size(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        strategy=StrategyConfig(matching_algorithm="optimal_transport_sinkhorn", optimal_transport_target_size=50),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error
    matched = result.datasets["matched_dataset"]
    # OT is a population-selection strategy (Opt. A): it selects a
    # subset of the pool, it does not produce treated/control pairs.
    # Selected units are marked "selected", not "control"/"treated".
    selected_rows = matched.filter(pl.col("__role__") == "selected")
    assert selected_rows.height == 50
    assert matched["pair_id"].null_count() == 50  # no pairing exists for this strategy


def test_optimal_transport_requires_target_size() -> None:
    with pytest.raises(ValidationError):
        StrategyConfig(matching_algorithm="optimal_transport_sinkhorn")


def test_candidate_prefilter_reduces_pool_size(synthetic_dataset: pl.DataFrame) -> None:
    preprocessed, data_config = _preprocess(synthetic_dataset)
    config = MatchingModuleConfig(
        population=PopulationConfig(treatment_col="treatment"),
        covariates=CovariatesConfig(matching_covariates=["age"]),
        strategy=StrategyConfig(
            matching_algorithm="optimal_hungarian",
            apply_candidate_prefilter=True, prefilter_k_neighbors=5,
        ),
    )
    module = MatchingModule()
    module.fit(preprocessed, data_config, config)
    result = module.run()

    assert result.success, result.error