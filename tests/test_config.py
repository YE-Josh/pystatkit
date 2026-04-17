"""Tests for v0.2 hierarchical config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pystatkit.core.config import StudyConfig, load_config


def _write_config(tmp_path: Path, raw: dict) -> Path:
    # Ensure the data file referenced exists so DataConfig doesn't choke.
    data_file = tmp_path / (raw.get("data", {}).get("file", "data.csv"))
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("subject_id,group,score\n")
    raw.setdefault("data", {})["file"] = str(data_file)

    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


def test_minimal_config_with_one_method(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "study": {"name": "Test study"},
            "data": {"file": "data.csv"},
            "methods": {
                "two_group": {
                    "enabled": True,
                    "outcome": "score",
                    "group": "group",
                    "method": "welch_t",
                }
            },
        },
    )
    cfg = load_config(cfg_path)
    assert isinstance(cfg, StudyConfig)
    enabled = list(cfg.enabled_methods())
    assert len(enabled) == 1
    assert enabled[0].name == "two_group"


def test_multiple_methods_preserve_order(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    data_file = tmp_path / "data.csv"
    data_file.write_text("subject_id,group,score\n")
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "data": {"file": str(data_file)},
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
                        "group": "group",
                        "method": "anova",
                    },
                },
            },
            sort_keys=False,  # preserve YAML order
        )
    )
    cfg = load_config(cfg_path)
    enabled_names = [m.name for m in cfg.enabled_methods()]
    assert enabled_names == ["two_group", "anova_oneway"]


def test_disabled_methods_excluded(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "two_group": {
                    "enabled": False,
                    "outcome": "x",
                    "group": "g",
                    "method": "welch_t",
                },
                "paired": {
                    "enabled": True,
                    "outcome": "x",
                    "condition": "c",
                    "method": "paired_t",
                },
            },
        },
    )
    cfg = load_config(cfg_path)
    enabled_names = [m.name for m in cfg.enabled_methods()]
    assert enabled_names == ["paired"]


def test_no_enabled_methods_raises(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "two_group": {"enabled": False, "outcome": "x", "group": "g"}
            },
        },
    )
    with pytest.raises(ValueError, match="No methods are enabled"):
        load_config(cfg_path)


def test_two_group_rejects_missing_method(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "two_group": {
                    "enabled": True,
                    "outcome": "score",
                    "group": "group",
                    # no method specified
                }
            },
        },
    )
    with pytest.raises(ValueError, match="two_group.method"):
        load_config(cfg_path)


def test_paired_rejects_wrong_method(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "paired": {
                    "enabled": True,
                    "outcome": "x",
                    "condition": "c",
                    "method": "welch_t",  # wrong family
                }
            },
        },
    )
    with pytest.raises(ValueError, match="paired.method"):
        load_config(cfg_path)


def test_unknown_method_in_yaml_warns_but_passes(tmp_path, capsys):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "mystery_method": {"enabled": True},
                "two_group": {
                    "enabled": True,
                    "outcome": "x",
                    "group": "g",
                    "method": "welch_t",
                },
            },
        },
    )
    cfg = load_config(cfg_path)
    captured = capsys.readouterr()
    assert "unknown method 'mystery_method'" in captured.out
    assert [m.name for m in cfg.enabled_methods()] == ["two_group"]


def test_unknown_field_warns(tmp_path, capsys):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "defaults": {"alpha": 0.05, "typo_field": 123},
            "methods": {
                "two_group": {
                    "enabled": True,
                    "outcome": "x",
                    "group": "g",
                    "method": "welch_t",
                }
            },
        },
    )
    load_config(cfg_path)
    captured = capsys.readouterr()
    assert "typo_field" in captured.out


def test_invalid_alpha(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "defaults": {"alpha": 1.5},
            "methods": {
                "two_group": {
                    "enabled": True,
                    "outcome": "x",
                    "group": "g",
                    "method": "welch_t",
                }
            },
        },
    )
    with pytest.raises(ValueError, match="alpha"):
        load_config(cfg_path)


def test_correlation_requires_two_vars(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {"correlation": {"enabled": True, "vars": ["age"]}},
        },
    )
    with pytest.raises(ValueError, match="at least 2 variables"):
        load_config(cfg_path)


def test_ancova_requires_covariate(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "data": {"file": "data.csv"},
            "methods": {
                "ancova": {
                    "enabled": True,
                    "outcome": "y",
                    "group": "g",
                    "covariates": [],
                }
            },
        },
    )
    with pytest.raises(ValueError, match="at least one covariate"):
        load_config(cfg_path)
