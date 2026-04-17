"""Tests for config loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pystatkit.core.config import AnalysisConfig, load_config


def _write_config(tmp_path: Path, data: dict) -> Path:
    # Create a dummy data file so path coercion doesn't fail loader tests.
    data_file = tmp_path / "data.csv"
    data_file.write_text("subject,group,score\n")
    data.setdefault("data_file", str(data_file))
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def test_load_valid_two_group_config(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "design": "two_group_independent",
            "method": "welch_t",
            "dv": "score",
            "group": "group",
            "output_name": "result",
        },
    )
    cfg = load_config(cfg_path)
    assert cfg.method == "welch_t"
    assert cfg.group == "group"


def test_paired_requires_subject_and_condition(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "design": "two_group_paired",
            "method": "paired_t",
            "dv": "score",
            "output_name": "result",
        },
    )
    with pytest.raises(ValueError, match="subject.*condition"):
        load_config(cfg_path)


def test_independent_requires_group(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "design": "two_group_independent",
            "method": "welch_t",
            "dv": "score",
            "output_name": "result",
        },
    )
    with pytest.raises(ValueError, match="group"):
        load_config(cfg_path)


def test_invalid_method_for_design(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "design": "two_group_independent",
            "method": "wilcoxon",  # paired method, wrong design
            "dv": "score",
            "group": "group",
            "output_name": "result",
        },
    )
    with pytest.raises(ValueError, match="not valid for design"):
        load_config(cfg_path)


def test_invalid_alpha(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {
            "design": "two_group_independent",
            "method": "welch_t",
            "dv": "score",
            "group": "group",
            "output_name": "result",
            "alpha": 1.5,
        },
    )
    with pytest.raises(ValueError, match="alpha"):
        load_config(cfg_path)
