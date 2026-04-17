"""Tests for one-way ANOVA and Kruskal-Wallis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnalysisConfig
from pystatkit.methods.one_way_anova import kruskal_wallis, one_way_anova


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


@pytest.fixture
def anova_config(tmp_path) -> AnalysisConfig:
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("placeholder")
    return AnalysisConfig(
        data_file=dummy,
        design="one_way_anova",
        method="anova",
        dv="score",
        group="group",
        posthoc="tukey",
        output_name="test",
        confirm_method=False,
    )


def test_anova_matches_pingouin(three_group_df, anova_config):
    result = one_way_anova(three_group_df, anova_config)
    direct = pg.anova(data=three_group_df, dv="score", between="group", detailed=True)

    assert np.isclose(result.primary["F"].iloc[0], direct["F"].iloc[0])
    assert np.isclose(result.primary["p_unc"].iloc[0], direct["p_unc"].iloc[0])


def test_anova_includes_tukey_posthoc(three_group_df, anova_config):
    result = one_way_anova(three_group_df, anova_config)
    assert result.posthoc is not None
    # 3 groups → 3 pairwise comparisons.
    assert len(result.posthoc) == 3


def test_anova_games_howell(three_group_df, anova_config):
    anova_config.posthoc = "games_howell"
    result = one_way_anova(three_group_df, anova_config)
    assert result.posthoc is not None
    assert len(result.posthoc) == 3


def test_anova_no_posthoc(three_group_df, anova_config):
    anova_config.posthoc = "none"
    result = one_way_anova(three_group_df, anova_config)
    assert result.posthoc is None


def test_kruskal_wallis_matches_pingouin(three_group_df, anova_config):
    anova_config.method = "kruskal_wallis"
    anova_config.posthoc = "dunn"
    result = kruskal_wallis(three_group_df, anova_config)
    direct = pg.kruskal(data=three_group_df, dv="score", between="group")

    assert np.isclose(result.primary["H"].iloc[0], direct["H"].iloc[0])


def test_effect_size_present(three_group_df, anova_config):
    result = one_way_anova(three_group_df, anova_config)
    assert "partial_eta_sq" in result.effect_size
    assert 0 <= result.effect_size["partial_eta_sq"] <= 1
