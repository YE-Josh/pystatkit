"""Tests for repeated-measures ANOVA."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnovaRMConfig
from pystatkit.methods.anova_rm import rm_anova


@pytest.fixture
def rm_df() -> pd.DataFrame:
    """20 subjects × 3 time points with a real time effect."""
    rng = np.random.default_rng(0)
    n = 20
    rows = []
    for i in range(n):
        base = rng.normal(100, 15)
        for t, offset in [("T1", 0), ("T2", 5), ("T3", 10)]:
            rows.append(
                {
                    "subject_id": f"S{i:02d}",
                    "time": t,
                    "score": base + offset + rng.normal(0, 5),
                }
            )
    return pd.DataFrame(rows)


def _cfg(**overrides) -> AnovaRMConfig:
    base = dict(
        enabled=True, outcome="score", within=["time"],
        sphericity_correction="gg", posthoc="holm",
    )
    base.update(overrides)
    return AnovaRMConfig(**base)


def test_rm_anova_matches_pingouin(rm_df):
    result = rm_anova(rm_df, _cfg(), id_col="subject_id")
    direct = pg.rm_anova(
        data=rm_df, dv="score", within="time", subject="subject_id",
        detailed=True, correction=True, effsize="np2",
    )
    assert np.isclose(result.primary["F"].iloc[0], direct["F"].iloc[0])


def test_rm_anova_returns_sphericity_info(rm_df):
    result = rm_anova(rm_df, _cfg(), id_col="subject_id")
    sph = result.extras["sphericity"]
    assert "mauchly_W" in sph
    assert "epsilon_gg" in sph


def test_rm_anova_posthoc(rm_df):
    result = rm_anova(rm_df, _cfg(posthoc="holm"), id_col="subject_id")
    assert result.posthoc is not None
    # 3 time points → 3 pairwise comparisons.
    assert len(result.posthoc) == 3


def test_rm_anova_no_posthoc(rm_df):
    result = rm_anova(rm_df, _cfg(posthoc="none"), id_col="subject_id")
    assert result.posthoc is None


def test_rm_anova_interpretation_apa(rm_df):
    result = rm_anova(rm_df, _cfg(), id_col="subject_id")
    assert "p = 0." not in result.interpretation
    assert "partial eta-squared" in result.interpretation


def test_rm_anova_n_counts_subjects(rm_df):
    result = rm_anova(rm_df, _cfg(), id_col="subject_id")
    assert result.n_total == 20  # subjects, not observations
