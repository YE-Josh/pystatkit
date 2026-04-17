"""End-to-end orchestrator tests: one config running multiple methods."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from pystatkit.core.config import load_config
from pystatkit.core.data_loader import load_data
from pystatkit.core.orchestrator import run_study


@pytest.fixture
def synthetic_data(tmp_path) -> Path:
    """Create a long-format dataset with 2 groups and a 3-level factor."""
    rng = np.random.default_rng(0)
    n_per_group = 30
    rows = []
    for grp, mean in [("HC", 10.0), ("PwP", 13.0)]:
        for i in range(n_per_group):
            rows.append(
                {
                    "subject_id": f"{grp}{i:02d}",
                    "group": grp,
                    "difficulty": rng.choice(["easy", "medium", "hard"]),
                    "score": rng.normal(mean, 2.0),
                }
            )
    df = pd.DataFrame(rows)
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)
    return path


def test_orchestrator_runs_multiple_methods(synthetic_data, tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "study": {"name": "Orchestrator test"},
                "data": {"file": str(synthetic_data)},
                "output": {"dir": str(tmp_path / "out"), "basename": "test"},
                "defaults": {"confirm_method": False},
                "methods": {
                    "two_group": {
                        "enabled": True,
                        "outcome": "score",
                        "group": "group",
                        "method": "welch_t",
                    },
                    "anova_oneway": {
                        "enabled": True,
                        "outcome": "score",
                        "group": "difficulty",
                        "method": "anova",
                        "posthoc": "tukey",
                    },
                },
            },
            sort_keys=False,
        )
    )

    cfg = load_config(cfg_path)
    df = load_data(cfg)
    runs = run_study(df, cfg, confirm_callback=None)

    assert len(runs) == 2
    assert all(not r.skipped for r in runs)
    assert runs[0].method_key == "two_group"
    assert runs[1].method_key == "anova_oneway"
    assert runs[0].result is not None
    assert runs[1].result is not None


def test_orchestrator_skips_on_missing_column(synthetic_data, tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "data": {"file": str(synthetic_data)},
                "output": {"dir": str(tmp_path / "out")},
                "defaults": {"confirm_method": False},
                "methods": {
                    "two_group": {
                        "enabled": True,
                        "outcome": "nonexistent_col",
                        "group": "group",
                        "method": "welch_t",
                    }
                },
            }
        )
    )
    cfg = load_config(cfg_path)
    df = load_data(cfg)
    runs = run_study(df, cfg, confirm_callback=None)

    assert len(runs) == 1
    assert runs[0].skipped is True
    assert "nonexistent_col" in runs[0].skip_reason


def test_confirm_callback_can_skip(synthetic_data, tmp_path):
    """Returning False from confirm_callback should mark the method as skipped."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "data": {"file": str(synthetic_data)},
                "output": {"dir": str(tmp_path / "out")},
                "defaults": {"confirm_method": False},
                "methods": {
                    "two_group": {
                        "enabled": True,
                        "outcome": "score",
                        "group": "group",
                        "method": "welch_t",
                    }
                },
            }
        )
    )
    cfg = load_config(cfg_path)
    df = load_data(cfg)
    runs = run_study(df, cfg, confirm_callback=lambda name: False)

    assert len(runs) == 1
    assert runs[0].skipped is True
    assert "declined" in runs[0].skip_reason
