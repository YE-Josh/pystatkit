"""Tests for two-group methods, validated against direct pingouin calls."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnalysisConfig
from pystatkit.methods.two_group import independent_t, mann_whitney, welch_t


@pytest.fixture
def two_group_df() -> pd.DataFrame:
    """Synthetic two-group data with known properties."""
    rng = np.random.default_rng(42)
    n = 30
    group_a = rng.normal(loc=10.0, scale=2.0, size=n)
    group_b = rng.normal(loc=12.0, scale=2.5, size=n)
    return pd.DataFrame(
        {
            "score": np.concatenate([group_a, group_b]),
            "group": ["A"] * n + ["B"] * n,
        }
    )


@pytest.fixture
def two_group_config(tmp_path) -> AnalysisConfig:
    """Minimal config for two-group analysis."""
    # Create a dummy data file so path validation passes.
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("placeholder")
    return AnalysisConfig(
        data_file=dummy,
        design="two_group_independent",
        method="independent_t",
        dv="score",
        group="group",
        output_name="test",
        confirm_method=False,
    )


def test_independent_t_matches_pingouin(two_group_df, two_group_config):
    """Our wrapper must return the same t, p as a direct pingouin call."""
    result = independent_t(two_group_df, two_group_config)

    x = two_group_df.loc[two_group_df["group"] == "A", "score"].to_numpy()
    y = two_group_df.loc[two_group_df["group"] == "B", "score"].to_numpy()
    direct = pg.ttest(x, y, paired=False, correction=False)

    assert np.isclose(result.primary["T"].iloc[0], direct["T"].iloc[0])
    assert np.isclose(result.primary["p_val"].iloc[0], direct["p_val"].iloc[0])


def test_welch_t_uses_correction(two_group_df, two_group_config):
    """Welch's t should apply the correction flag and have non-integer df."""
    two_group_config.method = "welch_t"
    result = welch_t(two_group_df, two_group_config)
    assert result.extras["welch_correction"] is True
    # Welch's correction typically gives non-integer df.
    assert result.primary["dof"].iloc[0] != int(result.primary["dof"].iloc[0])


def test_mann_whitney_matches_pingouin(two_group_df, two_group_config):
    two_group_config.method = "mann_whitney"
    result = mann_whitney(two_group_df, two_group_config)

    x = two_group_df.loc[two_group_df["group"] == "A", "score"].to_numpy()
    y = two_group_df.loc[two_group_df["group"] == "B", "score"].to_numpy()
    direct = pg.mwu(x, y, alternative="two-sided")

    assert np.isclose(result.primary["U_val"].iloc[0], direct["U_val"].iloc[0])


def test_result_contains_descriptives(two_group_df, two_group_config):
    """Result must include per-group descriptives for APA table output."""
    result = independent_t(two_group_df, two_group_config)
    assert result.descriptives is not None
    assert set(result.descriptives.index) == {"A", "B"}
    assert {"n", "mean", "sd", "median"}.issubset(result.descriptives.columns)


def test_interpretation_is_apa_formatted(two_group_df, two_group_config):
    """The interpretation string should follow APA conventions."""
    result = independent_t(two_group_df, two_group_config)
    # APA: no leading zero on p-values.
    assert "p = 0." not in result.interpretation
    # Should include effect size.
    assert "Cohen's d" in result.interpretation


def test_rejects_more_than_two_groups(tmp_path):
    """Should raise a clear error if the grouping column has ≠ 2 levels."""
    df = pd.DataFrame({"score": [1.0, 2, 3, 4, 5, 6], "group": ["A", "B", "C"] * 2})
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("placeholder")
    cfg = AnalysisConfig(
        data_file=dummy,
        design="two_group_independent",
        method="independent_t",
        dv="score",
        group="group",
        output_name="test",
    )
    with pytest.raises(ValueError, match="Expected exactly 2 groups"):
        independent_t(df, cfg)
