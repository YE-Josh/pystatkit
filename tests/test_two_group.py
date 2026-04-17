"""Tests for two-group methods (v0.2 config API)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import TwoGroupConfig
from pystatkit.methods.two_group import independent_t, mann_whitney, welch_t


@pytest.fixture
def two_group_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 30
    a = rng.normal(10.0, 2.0, n)
    b = rng.normal(12.0, 2.5, n)
    return pd.DataFrame(
        {"score": np.concatenate([a, b]), "group": ["A"] * n + ["B"] * n}
    )


def _cfg(method: str, **overrides) -> TwoGroupConfig:
    base = dict(
        enabled=True, outcome="score", group="group", method=method
    )
    base.update(overrides)
    return TwoGroupConfig(**base)


def test_independent_t_matches_pingouin(two_group_df):
    cfg = _cfg("independent_t")
    result = independent_t(two_group_df, cfg)

    x = two_group_df.loc[two_group_df["group"] == "A", "score"].to_numpy()
    y = two_group_df.loc[two_group_df["group"] == "B", "score"].to_numpy()
    direct = pg.ttest(x, y, paired=False, correction=False)

    assert np.isclose(result.primary["T"].iloc[0], direct["T"].iloc[0])
    assert np.isclose(result.primary["p_val"].iloc[0], direct["p_val"].iloc[0])


def test_welch_t_has_non_integer_df(two_group_df):
    cfg = _cfg("welch_t")
    result = welch_t(two_group_df, cfg)
    assert result.extras["welch_correction"] is True
    dof = result.primary["dof"].iloc[0]
    assert dof != int(dof)


def test_mann_whitney_matches_pingouin(two_group_df):
    cfg = _cfg("mann_whitney")
    result = mann_whitney(two_group_df, cfg)

    x = two_group_df.loc[two_group_df["group"] == "A", "score"].to_numpy()
    y = two_group_df.loc[two_group_df["group"] == "B", "score"].to_numpy()
    direct = pg.mwu(x, y, alternative="two-sided")

    assert np.isclose(result.primary["U_val"].iloc[0], direct["U_val"].iloc[0])


def test_descriptives_present(two_group_df):
    result = independent_t(two_group_df, _cfg("independent_t"))
    assert result.descriptives is not None
    assert set(result.descriptives.index) == {"A", "B"}
    assert {"n", "mean", "sd", "median"}.issubset(result.descriptives.columns)


def test_apa_interpretation_format(two_group_df):
    result = independent_t(two_group_df, _cfg("independent_t"))
    assert "p = 0." not in result.interpretation  # APA: no leading zero
    assert "Cohen's d" in result.interpretation


def test_hedges_g_effect_size(two_group_df):
    cfg = _cfg("independent_t", effect_size="hedges_g")
    result = independent_t(two_group_df, cfg)
    assert "hedges_g" in result.effect_size
    assert "Hedges' g" in result.interpretation


def test_rejects_more_than_two_groups():
    df = pd.DataFrame({"score": [1.0, 2, 3, 4, 5, 6], "group": ["A", "B", "C"] * 2})
    with pytest.raises(ValueError, match="Expected exactly 2 groups"):
        independent_t(df, _cfg("independent_t"))


def test_alternative_greater(two_group_df):
    """Alternative hypothesis is passed through correctly."""
    cfg = _cfg("welch_t", alternative="greater")
    result = welch_t(two_group_df, cfg)
    assert result.extras["alternative"] == "greater"
