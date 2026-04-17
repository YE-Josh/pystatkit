"""Tests for demographic (Table 1) generation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pystatkit.core.config import DemographicConfig
from pystatkit.methods.demographic import demographic


@pytest.fixture
def demo_df() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    n = 40
    return pd.DataFrame(
        {
            "subject_id": [f"S{i:02d}" for i in range(n)],
            "group": ["HC"] * 20 + ["PwP"] * 20,
            "age": rng.normal(65, 10, n),
            "bmi": rng.normal(25, 4, n),
            "sex": rng.choice(["M", "F"], n),
        }
    )


def test_demographic_by_group(demo_df):
    cfg = DemographicConfig(
        enabled=True,
        group_by="group",
        continuous=["age", "bmi"],
        categorical=["sex"],
    )
    result = demographic(demo_df, cfg)
    assert result.n_total == 40
    assert result.primary is not None
    # Resulting table should contain columns for each group and a P-Value.
    cols = [str(c) for c in result.primary.columns]
    assert any("HC" in c for c in cols)
    assert any("PwP" in c for c in cols)


def test_demographic_no_groupby(demo_df):
    cfg = DemographicConfig(
        enabled=True,
        continuous=["age", "bmi"],
        categorical=["sex"],
    )
    result = demographic(demo_df, cfg)
    # Without groupby, should still produce a one-column summary.
    assert result.primary is not None
    assert result.n_total == 40


def test_demographic_dedup_long_format():
    """Long-format data with repeated rows per subject should dedupe."""
    df = pd.DataFrame(
        [
            {"subject_id": "S01", "group": "HC", "age": 60, "trial": 1, "score": 1.0},
            {"subject_id": "S01", "group": "HC", "age": 60, "trial": 2, "score": 2.0},
            {"subject_id": "S02", "group": "PwP", "age": 70, "trial": 1, "score": 3.0},
            {"subject_id": "S02", "group": "PwP", "age": 70, "trial": 2, "score": 4.0},
        ]
    )
    cfg = DemographicConfig(
        enabled=True, group_by="group", continuous=["age"], categorical=[]
    )
    result = demographic(df, cfg)
    # After dedup on [age, group], we should have 2 unique rows.
    assert result.n_total == 2


def test_demographic_median_iqr(demo_df):
    cfg = DemographicConfig(
        enabled=True,
        group_by="group",
        continuous=["age"],
        categorical=[],
        continuous_summary="median_iqr",
    )
    result = demographic(demo_df, cfg)
    # The row label should now say "median [Q1,Q3]" rather than "mean (SD)".
    index_strs = [str(i) for i in result.primary.iloc[:, 0]]
    assert any("median" in s.lower() for s in index_strs)


def test_demographic_requires_at_least_one_var():
    cfg = DemographicConfig(enabled=True, continuous=[], categorical=[])
    with pytest.raises(ValueError, match="at least one"):
        cfg.validate()
