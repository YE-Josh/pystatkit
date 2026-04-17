"""Tests for correlation method."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pystatkit.core.config import CorrelationConfig
from pystatkit.methods.correlation import correlation


@pytest.fixture
def corr_df() -> pd.DataFrame:
    rng = np.random.default_rng(2)
    n = 50
    x = rng.normal(0, 1, n)
    y = x * 0.7 + rng.normal(0, 0.6, n)  # correlated with x
    z = rng.normal(0, 1, n)              # independent
    return pd.DataFrame({"x": x, "y": y, "z": z})


def test_pearson_matrix(corr_df):
    cfg = CorrelationConfig(enabled=True, vars=["x", "y", "z"], method="pearson")
    result = correlation(corr_df, cfg)
    assert result.primary is not None
    # 3 variables → 3 pairwise correlations.
    assert len(result.primary) == 3
    # Matrix should also be attached.
    matrix = result.extras["matrix"]
    assert matrix.shape == (3, 3)
    assert np.isclose(matrix.loc["x", "x"], 1.0)


def test_spearman_runs(corr_df):
    cfg = CorrelationConfig(enabled=True, vars=["x", "y"], method="spearman")
    result = correlation(corr_df, cfg)
    assert "spearman" in result.method.lower()


def test_kendall_runs(corr_df):
    cfg = CorrelationConfig(enabled=True, vars=["x", "y"], method="kendall")
    result = correlation(corr_df, cfg)
    assert "kendall" in result.method.lower()


def test_requires_two_vars():
    cfg = CorrelationConfig(enabled=True, vars=["x"])
    with pytest.raises(ValueError, match="at least 2 variables"):
        cfg.validate()


def test_interpretation_counts_significant(corr_df):
    cfg = CorrelationConfig(enabled=True, vars=["x", "y", "z"], method="pearson")
    result = correlation(corr_df, cfg)
    # x-y should be significant; x-z and y-z should not. Expect "1 of 3".
    assert "1 of 3" in result.interpretation or "2 of 3" in result.interpretation
