"""Tests for paired methods (v0.2 API)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import PairedConfig
from pystatkit.methods.paired import paired_t, wilcoxon


@pytest.fixture
def paired_df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 25
    pre = rng.normal(50.0, 10.0, n)
    post = pre + rng.normal(5.0, 3.0, n)
    rows = []
    for i in range(n):
        rows.append({"subject_id": f"S{i:02d}", "condition": "pre", "score": pre[i]})
        rows.append({"subject_id": f"S{i:02d}", "condition": "post", "score": post[i]})
    return pd.DataFrame(rows)


def _cfg(method: str, **overrides) -> PairedConfig:
    base = dict(
        enabled=True, outcome="score", condition="condition", method=method
    )
    base.update(overrides)
    return PairedConfig(**base)


def test_paired_t_matches_pingouin(paired_df):
    result = paired_t(paired_df, _cfg("paired_t"), id_col="subject_id")

    wide = paired_df.pivot_table(index="subject_id", columns="condition", values="score")
    c1, c2 = wide.columns[0], wide.columns[1]
    direct = pg.ttest(wide[c1], wide[c2], paired=True)

    assert np.isclose(result.primary["T"].iloc[0], direct["T"].iloc[0])


def test_wilcoxon_runs(paired_df):
    result = wilcoxon(paired_df, _cfg("wilcoxon"), id_col="subject_id")
    assert "p_val" in result.primary.columns
    assert result.n_total == 25


def test_drops_incomplete_pairs():
    df = pd.DataFrame(
        [
            {"subject_id": "S01", "condition": "pre", "score": 10.0},
            {"subject_id": "S01", "condition": "post", "score": 12.0},
            {"subject_id": "S02", "condition": "pre", "score": 9.0},  # no post
            {"subject_id": "S03", "condition": "pre", "score": 11.0},
            {"subject_id": "S03", "condition": "post", "score": 14.0},
        ]
    )
    result = paired_t(df, _cfg("paired_t"), id_col="subject_id")
    assert result.n_total == 2  # S01 + S03


def test_custom_id_column(paired_df):
    df = paired_df.rename(columns={"subject_id": "participant"})
    cfg = _cfg("paired_t", id="participant")
    result = paired_t(df, cfg, id_col="subject_id")  # id in cfg overrides default
    assert result.n_total == 25
