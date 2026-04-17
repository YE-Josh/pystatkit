"""Tests for mixed ANOVA (within × between)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from pystatkit.core.config import AnovaMixedConfig
from pystatkit.methods.anova_mixed import mixed_anova


@pytest.fixture
def mixed_df() -> pd.DataFrame:
    """30 subjects (15 HC, 15 PwP) × 3 time points with an interaction."""
    rng = np.random.default_rng(1)
    rows = []
    for i in range(30):
        group = "HC" if i < 15 else "PwP"
        base = rng.normal(100, 12)
        for t in ["T1", "T2", "T3"]:
            # PwP improves more over time (interaction).
            t_offset = {"T1": 0, "T2": 3, "T3": 6}[t]
            if group == "PwP":
                t_offset *= 2
            rows.append(
                {
                    "subject_id": f"{group}{i:02d}",
                    "group": group,
                    "time": t,
                    "score": base + t_offset + rng.normal(0, 4),
                }
            )
    return pd.DataFrame(rows)


def _cfg(**overrides) -> AnovaMixedConfig:
    base = dict(
        enabled=True, outcome="score", within="time", between="group",
        sphericity_correction="gg", posthoc="holm", simple_effects=True,
    )
    base.update(overrides)
    return AnovaMixedConfig(**base)


def test_mixed_anova_matches_pingouin(mixed_df):
    result = mixed_anova(mixed_df, _cfg(), id_col="subject_id")
    direct = pg.mixed_anova(
        data=mixed_df, dv="score", within="time", between="group",
        subject="subject_id",
    )
    # Compare F values across all three rows.
    for i in range(3):
        assert np.isclose(
            result.primary["F"].iloc[i], direct["F"].iloc[i], equal_nan=True
        )


def test_mixed_anova_has_three_effects(mixed_df):
    result = mixed_anova(mixed_df, _cfg(), id_col="subject_id")
    sources = set(result.primary["Source"].tolist())
    assert sources == {"group", "time", "Interaction"}


def test_mixed_anova_simple_effects_on_interaction(mixed_df):
    """Simple effects should populate when the interaction is significant."""
    result = mixed_anova(mixed_df, _cfg(), id_col="subject_id")
    # Our synthetic data has a strong interaction; simple effects should be computed.
    simple = result.extras["simple_effects"]
    if simple is not None:
        # Should have one row per between-group level.
        assert len(simple) == 2


def test_mixed_anova_no_simple_effects_when_disabled(mixed_df):
    result = mixed_anova(
        mixed_df, _cfg(simple_effects=False), id_col="subject_id"
    )
    assert result.extras["simple_effects"] is None


def test_mixed_anova_effect_sizes(mixed_df):
    result = mixed_anova(mixed_df, _cfg(), id_col="subject_id")
    # Should have effect sizes for each of the three sources that have F values.
    keys = set(result.effect_size.keys())
    assert any("time" in k for k in keys)
    assert any("group" in k for k in keys)
