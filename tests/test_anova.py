"""Tests for one-way ANOVA methods (v0.2 API)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnovaOnewayConfig
from pystatkit.methods.one_way_anova import (
    kruskal_wallis,
    one_way_anova,
    welch_anova,
)


@pytest.fixture
def three_group_df() -> pd.DataFrame:
    rng = np.random.default_rng(123)
    n = 25
    g1 = rng.normal(10, 2, n)
    g2 = rng.normal(12, 2, n)
    g3 = rng.normal(15, 2, n)
    return pd.DataFrame(
        {
            "score": np.concatenate([g1, g2, g3]),
            "group": ["A"] * n + ["B"] * n + ["C"] * n,
        }
    )


def _cfg(method: str, **overrides) -> AnovaOnewayConfig:
    base = dict(
        enabled=True, outcome="score", group="group", method=method,
        posthoc="tukey",
    )
    base.update(overrides)
    return AnovaOnewayConfig(**base)


def test_anova_matches_pingouin(three_group_df):
    result = one_way_anova(three_group_df, _cfg("anova"))
    direct = pg.anova(data=three_group_df, dv="score", between="group", detailed=True)
    assert np.isclose(result.primary["F"].iloc[0], direct["F"].iloc[0])


def test_anova_tukey_posthoc(three_group_df):
    result = one_way_anova(three_group_df, _cfg("anova", posthoc="tukey"))
    assert result.posthoc is not None
    assert len(result.posthoc) == 3  # 3 pairwise comparisons for 3 groups


def test_anova_games_howell(three_group_df):
    result = one_way_anova(three_group_df, _cfg("anova", posthoc="games_howell"))
    assert result.posthoc is not None
    assert len(result.posthoc) == 3


def test_anova_no_posthoc(three_group_df):
    result = one_way_anova(three_group_df, _cfg("anova", posthoc="none"))
    assert result.posthoc is None


def test_welch_anova_runs(three_group_df):
    result = welch_anova(three_group_df, _cfg("welch_anova"))
    assert "F" in result.primary.columns
    assert result.method_key == "welch_anova"
    # Games-Howell is automatically used for Welch.
    assert result.posthoc is not None


def test_kruskal_matches_pingouin(three_group_df):
    cfg = _cfg("kruskal_wallis", posthoc="dunn")
    result = kruskal_wallis(three_group_df, cfg)
    direct = pg.kruskal(data=three_group_df, dv="score", between="group")
    assert np.isclose(result.primary["H"].iloc[0], direct["H"].iloc[0])


def test_effect_size_in_range(three_group_df):
    result = one_way_anova(three_group_df, _cfg("anova"))
    assert 0 <= result.effect_size["partial_eta_sq"] <= 1
