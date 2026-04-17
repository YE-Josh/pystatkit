"""Configuration schema and loader.

A single YAML file describes an entire analysis: data location, variables,
chosen method, and output preferences. This keeps analyses reproducible —
the config itself is the record of what was run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Registry of methods supported in v0.1.
# Grouped by design type; the config validator uses this to check method validity.
SUPPORTED_METHODS: dict[str, list[str]] = {
    "two_group_independent": ["independent_t", "welch_t", "mann_whitney"],
    "two_group_paired": ["paired_t", "wilcoxon"],
    "one_way_anova": ["anova", "kruskal_wallis"],
}

# Post-hoc methods valid for one-way ANOVA family.
SUPPORTED_POSTHOC: list[str] = ["tukey", "games_howell", "dunn", "none"]


@dataclass
class AnalysisConfig:
    """Full specification of a single analysis run.

    Attributes
    ----------
    data_file : Path
        Path to the input data file (.csv or .xlsx).
    sheet : str | None
        Sheet name for .xlsx inputs. Ignored for .csv.
    design : str
        One of: 'two_group_independent', 'two_group_paired', 'one_way_anova'.
    method : str
        Statistical method to apply. Must be valid for the chosen design.
    dv : str
        Dependent variable column name.
    group : str | None
        Grouping column (for independent designs and ANOVA).
    subject : str | None
        Subject ID column (required for paired designs).
    condition : str | None
        Within-subject condition column (required for paired designs).
    posthoc : str
        Post-hoc method for ANOVA. Default 'tukey'.
    output_dir : Path
        Directory for output files.
    output_name : str
        Base filename for output tables.
    alpha : float
        Significance level. Default 0.05.
    confirm_method : bool
        If True, prompt the user to confirm after assumption checks.
    """

    data_file: Path
    design: str
    method: str
    dv: str
    output_name: str
    sheet: str | None = None
    group: str | None = None
    subject: str | None = None
    condition: str | None = None
    posthoc: str = "tukey"
    output_dir: Path = field(default_factory=lambda: Path("outputs/tables"))
    alpha: float = 0.05
    confirm_method: bool = True

    def __post_init__(self) -> None:
        # Coerce paths (YAML gives strings).
        self.data_file = Path(self.data_file)
        self.output_dir = Path(self.output_dir)
        self._validate()

    def _validate(self) -> None:
        if self.design not in SUPPORTED_METHODS:
            raise ValueError(
                f"Unknown design '{self.design}'. "
                f"Supported: {list(SUPPORTED_METHODS.keys())}"
            )
        valid_methods = SUPPORTED_METHODS[self.design]
        if self.method not in valid_methods:
            raise ValueError(
                f"Method '{self.method}' is not valid for design '{self.design}'. "
                f"Valid methods: {valid_methods}"
            )
        if self.design == "two_group_paired":
            if not self.subject or not self.condition:
                raise ValueError(
                    "Paired design requires both 'subject' and 'condition' columns."
                )
        if self.design in ("two_group_independent", "one_way_anova"):
            if not self.group:
                raise ValueError(
                    f"Design '{self.design}' requires a 'group' column."
                )
        if self.posthoc not in SUPPORTED_POSTHOC:
            raise ValueError(
                f"Unknown post-hoc method '{self.posthoc}'. "
                f"Supported: {SUPPORTED_POSTHOC}"
            )
        if not 0 < self.alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {self.alpha}")


def load_config(path: str | Path) -> AnalysisConfig:
    """Load an AnalysisConfig from a YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the YAML configuration file.

    Returns
    -------
    AnalysisConfig
        The parsed and validated configuration.

    Examples
    --------
    >>> cfg = load_config("examples/study_example/config/two_group.yaml")
    >>> cfg.method
    'welch_t'
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return AnalysisConfig(**data)
