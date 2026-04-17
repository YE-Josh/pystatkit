"""Tests for ANCOVA."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AncovaAssumptions, AncovaConfig
from pystatkit.methods.ancova import ancova


@pytest.fixture
def ancova_df() -> pd.DataFrame:
    """Three groups; outcome depends on group + baseline covariate."""
    rng = np.random.default_rng(3)
    n = 60
    group = rng.choice(["A", "B", "C"], n)
    baseline = rng.normal(50, 10, n)
    group_offset = np.where(group == "A", 0, np.where(group == "B", 5, 10))
    outcome = 0.6 * baseline + group_offset + rng.normal(0, 5, n)
    return pd.DataFrame(
        {"group": group, "baseline": baseline, "outcome": outcome}
    )


def _cfg(**overrides) -> AncovaConfig:
    base = dict(
        enabled=True, outcome="outcome", group="group",
        covariates=["baseline"], posthoc="holm",
    )
    base.update(overrides)
    return AncovaConfig(**base)


def test_ancova_matches_pingouin(ancova_df):
    result = ancova(ancova_df, _cfg())
    direct = pg.ancova(
        data=ancova_df, dv="outcome", covar="baseline", between="group"
    )
    group_row = result.primary[result.primary["Source"] == "group"].iloc[0]
    direct_row = direct[direct["Source"] == "group"].iloc[0]
    assert np.isclose(group_row["F"], direct_row["F"])


def test_ancova_adjusted_means(ancova_df):
    result = ancova(ancova_df, _cfg())
    adj = result.extras["adjusted_means"]
    assert adj is not None
    # Three groups → three rows.
    assert len(adj) == 3
    assert {"adjusted_mean", "se", "ci_low", "ci_high"}.issubset(adj.columns)


def test_ancova_no_adjusted_means(ancova_df):
    result = ancova(ancova_df, _cfg(adjusted_means=False))
    assert result.extras["adjusted_means"] is None


def test_ancova_homogeneity_of_slopes(ancova_df):
    result = ancova(ancova_df, _cfg())
    slopes = result.extras["assumptions"]["homogeneity_of_slopes"]
    # Should have one interaction term per dummy-coded contrast (G-1 terms).
    assert len(slopes) >= 1
    assert "pval" in slopes.columns


def test_ancova_residual_normality(ancova_df):
    result = ancova(ancova_df, _cfg())
    norm = result.extras["assumptions"]["normality_residuals"]
    assert "pval" in norm.columns


def test_ancova_skips_assumptions_when_disabled(ancova_df):
    cfg = _cfg(
        check_assumptions=AncovaAssumptions(
            homogeneity_of_slopes=False,
            linearity=False,
            normality_residuals=False,
            homogeneity_variance=False,
        ),
    )
    result = ancova(ancova_df, cfg)
    assert result.extras["assumptions"] == {}


def test_ancova_requires_covariate():
    cfg = AncovaConfig(enabled=True, outcome="y", group="g", covariates=[])
    with pytest.raises(ValueError, match="at least one covariate"):
        cfg.validate()


def test_ancova_multiple_covariates(ancova_df):
    rng = np.random.default_rng(99)
    ancova_df = ancova_df.copy()
    ancova_df["age"] = rng.normal(65, 8, len(ancova_df))
    result = ancova(ancova_df, _cfg(covariates=["baseline", "age"]))
    covariate_rows = result.primary[
        result.primary["Source"].isin(["baseline", "age"])
    ]
    assert len(covariate_rows) == 2
