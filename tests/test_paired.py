"""Tests for paired methods."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnalysisConfig
from pystatkit.methods.paired import paired_t, wilcoxon


@pytest.fixture
def paired_df() -> pd.DataFrame:
    """Synthetic paired data: each subject measured under two conditions."""
    rng = np.random.default_rng(7)
    n = 25
    pre = rng.normal(loc=50.0, scale=10.0, size=n)
    # Add a small positive effect of "post".
    post = pre + rng.normal(loc=5.0, scale=3.0, size=n)
    rows = []
    for i in range(n):
        rows.append({"subject": f"S{i:02d}", "condition": "pre", "score": pre[i]})
        rows.append({"subject": f"S{i:02d}", "condition": "post", "score": post[i]})
    return pd.DataFrame(rows)


@pytest.fixture
def paired_config(tmp_path) -> AnalysisConfig:
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("placeholder")
    return AnalysisConfig(
        data_file=dummy,
        design="two_group_paired",
        method="paired_t",
        dv="score",
        subject="subject",
        condition="condition",
        output_name="test",
        confirm_method=False,
    )


def test_paired_t_matches_pingouin(paired_df, paired_config):
    result = paired_t(paired_df, paired_config)

    wide = paired_df.pivot_table(index="subject", columns="condition", values="score")
    c1, c2 = wide.columns[0], wide.columns[1]
    direct = pg.ttest(wide[c1], wide[c2], paired=True)

    assert np.isclose(result.primary["T"].iloc[0], direct["T"].iloc[0])
    assert np.isclose(result.primary["p_val"].iloc[0], direct["p_val"].iloc[0])


def test_wilcoxon_runs(paired_df, paired_config):
    paired_config.method = "wilcoxon"
    result = wilcoxon(paired_df, paired_config)
    assert "p_val" in result.primary.columns
    assert result.n_total == 25


def test_paired_handles_missing_pair(paired_config):
    """If a subject has only one condition, they should be dropped with a note."""
    df = pd.DataFrame(
        [
            {"subject": "S01", "condition": "pre", "score": 10.0},
            {"subject": "S01", "condition": "post", "score": 12.0},
            {"subject": "S02", "condition": "pre", "score": 9.0},
            # S02 missing 'post'
            {"subject": "S03", "condition": "pre", "score": 11.0},
            {"subject": "S03", "condition": "post", "score": 14.0},
        ]
    )
    result = paired_t(df, paired_config)
    assert result.n_total == 2  # S01 and S03 only
