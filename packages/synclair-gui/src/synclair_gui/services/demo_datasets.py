"""
synclair_gui.services.demo_datasets
----------------------------------------

Registry of small, deterministic synthetic datasets used only by the
public, unauthenticated demo endpoints (routers/demo.py). Kept separate
from the HTTP layer so datasets can later be swapped for static files
(e.g. synclair-gui/demo_data/*.csv) by changing only `build`, without
touching the router.

These datasets never touch dataset_store/job_manager: the demo is
stateless and anonymous by design (see routers/demo.py).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import polars as pl

__all__ = ["DemoDataset", "DEMO_DATASETS", "get_demo_dataset", "DemoDatasetNotFoundError"]


class DemoDatasetNotFoundError(Exception):
    """Raised when a requested demo dataset name is not in the known registry."""


@dataclass(frozen=True)
class DemoDataset:
    name: str
    title: str
    description: str
    build: Callable[[], pl.DataFrame]


def _build_blobs_2d() -> pl.DataFrame:
    """Three well-separated 2D Gaussian blobs -- the simplest possible
    visual proof that clustering works."""
    rng = np.random.default_rng(42)
    n_per_cluster = 20
    centers = [(0.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    xs: list[float] = []
    ys: list[float] = []
    for cx, cy in centers:
        xs.extend(rng.normal(cx, 0.6, n_per_cluster).tolist())
        ys.extend(rng.normal(cy, 0.6, n_per_cluster).tolist())
    return pl.DataFrame({"feature_1": xs, "feature_2": ys})


def _build_elongated_clusters() -> pl.DataFrame:
    """Two elongated/correlated clusters, less trivially separable than
    round blobs -- useful to show PCA doing something non-trivial."""
    rng = np.random.default_rng(7)
    n = 25
    x1 = rng.normal(0, 1.0, n)
    y1 = x1 * 0.6 + rng.normal(0, 0.3, n)
    x2 = rng.normal(9, 1.0, n)
    y2 = x2 * 0.6 + rng.normal(3, 0.3, n)
    return pl.DataFrame(
        {
            "feature_1": np.concatenate([x1, x2]).tolist(),
            "feature_2": np.concatenate([y1, y2]).tolist(),
        }
    )


def _build_clinical_like() -> pl.DataFrame:
    """Three numeric features loosely resembling clinical measurements
    (age, BMI, systolic BP), for a demo card closer to SynClair's actual
    domain than abstract points."""
    rng = np.random.default_rng(123)
    n = 20
    age_low = rng.normal(35, 4, n)
    bmi_low = rng.normal(22, 1.5, n)
    bp_low = rng.normal(115, 5, n)
    age_high = rng.normal(65, 5, n)
    bmi_high = rng.normal(31, 2.0, n)
    bp_high = rng.normal(145, 6, n)
    return pl.DataFrame(
        {
            "age": np.concatenate([age_low, age_high]).tolist(),
            "bmi": np.concatenate([bmi_low, bmi_high]).tolist(),
            "systolic_bp": np.concatenate([bp_low, bp_high]).tolist(),
        }
    )


DEMO_DATASETS: dict[str, DemoDataset] = {
    "blobs_2d": DemoDataset(
        name="blobs_2d",
        title="3 separated 2D blobs",
        description="Three clearly separated Gaussian clusters in 2D -- a quick sanity-check demo.",
        build=_build_blobs_2d,
    ),
    "elongated_clusters": DemoDataset(
        name="elongated_clusters",
        title="2 elongated clusters",
        description="Two correlated, elongated clusters -- shows PCA/clustering on less trivial shapes.",
        build=_build_elongated_clusters,
    ),
    "clinical_like": DemoDataset(
        name="clinical_like",
        title="Clinical-like measurements",
        description="Synthetic age/BMI/blood-pressure measurements forming two patient-like groups.",
        build=_build_clinical_like,
    ),
}


def get_demo_dataset(name: str) -> DemoDataset:
    dataset = DEMO_DATASETS.get(name)
    if dataset is None:
        raise DemoDatasetNotFoundError(f"Unknown demo dataset '{name}'. Known: {sorted(DEMO_DATASETS)}")
    return dataset