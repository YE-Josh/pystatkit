"""Configuration schema for v0.2.

Hierarchy
---------
    StudyConfig
    ├── study:     StudyMetadata
    ├── data:      DataConfig
    ├── defaults:  Defaults
    ├── output:    OutputConfig
    └── methods:   dict[str, MethodConfig]   # one entry per method

Each method has its own dataclass (TwoGroupConfig, PairedConfig, ...), so
method-specific validation lives with that method rather than in a single
flat class. `StudyConfig.enabled_methods()` yields only the methods with
`enabled: true`, preserving the order they appear in the YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Iterator

import yaml


# =============================================================================
# Top-level sub-configs
# =============================================================================

@dataclass
class StudyMetadata:
    """Metadata written into every output for provenance."""

    name: str = "Unnamed study"
    analyst: str = ""
    date: str = ""
    notes: str = ""


@dataclass
class DataConfig:
    """Data source specification."""

    file: Path = Path("data.csv")
    sheet: str | None = None
    format: str = "long"          # v0.2: only 'long' is supported
    id_col: str = "subject_id"

    def __post_init__(self) -> None:
        self.file = Path(self.file)
        if self.format != "long":
            raise ValueError(
                f"format='{self.format}' is not supported in v0.2. "
                "Only 'long' format is currently supported; convert wide data "
                "using pandas.melt() before calling pystatkit."
            )


@dataclass
class Defaults:
    """Global defaults, overridable per method."""

    alpha: float = 0.05
    ci_level: float = 0.95
    digits: int = 3
    na_policy: str = "listwise"   # listwise | pairwise
    p_adjust: str = "holm"        # none | bonferroni | holm | fdr_bh
    confirm_method: bool = True

    def __post_init__(self) -> None:
        if not 0 < self.alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {self.alpha}")
        if not 0 < self.ci_level < 1:
            raise ValueError(f"ci_level must be in (0, 1), got {self.ci_level}")
        if self.na_policy not in ("listwise", "pairwise"):
            raise ValueError(
                f"na_policy must be 'listwise' or 'pairwise', got '{self.na_policy}'"
            )
        if self.p_adjust not in ("none", "bonferroni", "holm", "fdr_bh"):
            raise ValueError(
                f"p_adjust must be one of "
                f"'none', 'bonferroni', 'holm', 'fdr_bh'; got '{self.p_adjust}'"
            )


@dataclass
class OutputConfig:
    """Where and how to write results."""

    dir: Path = field(default_factory=lambda: Path("./results"))
    basename: str = "analysis"
    formats: list[str] = field(default_factory=lambda: ["docx", "xlsx"])
    include_provenance: bool = True

    def __post_init__(self) -> None:
        self.dir = Path(self.dir)
        valid = {"docx", "xlsx", "csv"}
        bad = [f for f in self.formats if f not in valid]
        if bad:
            raise ValueError(f"Unknown output formats: {bad}. Valid: {sorted(valid)}")


# =============================================================================
# Method-specific configs
# =============================================================================

@dataclass
class MethodConfig:
    """Base class for per-method configs."""

    enabled: bool = False
    name: str = ""  # override in subclasses

    def validate(self) -> None:
        """Override to add method-specific validation."""
        return None


@dataclass
class DemographicConfig(MethodConfig):
    name: str = "demographic"
    group_by: str | None = None
    continuous: list[str] = field(default_factory=list)
    categorical: list[str] = field(default_factory=list)
    continuous_summary: str = "mean_sd"   # mean_sd | median_iqr | auto
    nonnormal: list[str] = field(default_factory=list)
    categorical_summary: str = "n_pct"
    include_tests: bool = True
    overall_column: bool = True

    def validate(self) -> None:
        if not self.enabled:
            return
        if not self.continuous and not self.categorical:
            raise ValueError(
                "demographic: at least one of `continuous` or `categorical` "
                "must be non-empty."
            )
        if self.continuous_summary not in ("mean_sd", "median_iqr", "auto"):
            raise ValueError(
                f"demographic.continuous_summary invalid: '{self.continuous_summary}'"
            )


@dataclass
class TwoGroupConfig(MethodConfig):
    name: str = "two_group"
    outcome: str | None = None
    group: str | None = None
    method: str | None = None             # independent_t | welch_t | mann_whitney
    alternative: str = "two_sided"
    normality_check: str = "shapiro"
    homogeneity_check: str = "levene_median"
    effect_size: str = "cohens_d"

    _VALID_METHODS = ("independent_t", "welch_t", "mann_whitney")

    def validate(self) -> None:
        if not self.enabled:
            return
        if self.outcome is None or self.group is None:
            raise ValueError("two_group requires 'outcome' and 'group'.")
        if self.method not in self._VALID_METHODS:
            raise ValueError(
                f"two_group.method must be one of {self._VALID_METHODS}, "
                f"got '{self.method}'. (There is no 'auto' — choose explicitly.)"
            )


@dataclass
class PairedConfig(MethodConfig):
    name: str = "paired"
    outcome: str | None = None
    condition: str | None = None
    id: str | None = None
    method: str | None = None             # paired_t | wilcoxon
    alternative: str = "two_sided"
    normality_check: str = "shapiro"
    effect_size: str = "cohens_dz"

    _VALID_METHODS = ("paired_t", "wilcoxon")

    def validate(self) -> None:
        if not self.enabled:
            return
        if self.outcome is None or self.condition is None:
            raise ValueError("paired requires 'outcome' and 'condition'.")
        if self.method not in self._VALID_METHODS:
            raise ValueError(
                f"paired.method must be one of {self._VALID_METHODS}, "
                f"got '{self.method}'."
            )


@dataclass
class AnovaOnewayConfig(MethodConfig):
    name: str = "anova_oneway"
    outcome: str | None = None
    group: str | None = None
    method: str | None = None             # anova | welch_anova | kruskal_wallis
    normality_check: str = "shapiro"
    homogeneity_check: str = "levene_median"
    posthoc: str = "tukey"
    effect_size: str = "partial_eta_sq"

    _VALID_METHODS = ("anova", "welch_anova", "kruskal_wallis")
    _VALID_POSTHOC = ("tukey", "games_howell", "dunn", "none")

    def validate(self) -> None:
        if not self.enabled:
            return
        if self.outcome is None or self.group is None:
            raise ValueError("anova_oneway requires 'outcome' and 'group'.")
        if self.method not in self._VALID_METHODS:
            raise ValueError(
                f"anova_oneway.method must be one of {self._VALID_METHODS}, "
                f"got '{self.method}'."
            )
        if self.posthoc not in self._VALID_POSTHOC:
            raise ValueError(
                f"anova_oneway.posthoc must be one of {self._VALID_POSTHOC}, "
                f"got '{self.posthoc}'."
            )


@dataclass
class AnovaRMConfig(MethodConfig):
    name: str = "anova_rm"
    outcome: str | None = None
    within: list[str] = field(default_factory=list)
    id: str | None = None
    sphericity_check: bool = True
    sphericity_correction: str = "gg"
    posthoc: str = "holm"
    effect_size: str = "partial_eta_sq"

    def validate(self) -> None:
        if not self.enabled:
            return
        if self.outcome is None:
            raise ValueError("anova_rm requires 'outcome'.")
        if not self.within:
            raise ValueError("anova_rm requires a non-empty 'within' list.")
        if self.sphericity_correction not in ("gg", "hf", "none"):
            raise ValueError(
                f"anova_rm.sphericity_correction must be 'gg', 'hf', or 'none'; "
                f"got '{self.sphericity_correction}'."
            )


@dataclass
class AnovaMixedConfig(MethodConfig):
    name: str = "anova_mixed"
    outcome: str | None = None
    within: str | None = None
    between: str | None = None
    id: str | None = None
    sphericity_check: bool = True
    sphericity_correction: str = "gg"
    posthoc: str = "holm"
    simple_effects: bool = True
    effect_size: str = "partial_eta_sq"

    def validate(self) -> None:
        if not self.enabled:
            return
        if not all([self.outcome, self.within, self.between]):
            raise ValueError(
                "anova_mixed requires 'outcome', 'within', and 'between'."
            )


@dataclass
class CorrelationConfig(MethodConfig):
    name: str = "correlation"
    vars: list[str] = field(default_factory=list)
    method: str = "pearson"
    ci: bool = True
    matrix_output: bool = True

    def validate(self) -> None:
        if not self.enabled:
            return
        if len(self.vars) < 2:
            raise ValueError(
                "correlation requires at least 2 variables in 'vars'."
            )
        if self.method not in ("pearson", "spearman", "kendall"):
            raise ValueError(
                f"correlation.method must be 'pearson', 'spearman', or 'kendall'; "
                f"got '{self.method}'."
            )


@dataclass
class AncovaAssumptions:
    homogeneity_of_slopes: bool = True
    linearity: bool = True
    normality_residuals: bool = True
    homogeneity_variance: bool = True


@dataclass
class AncovaConfig(MethodConfig):
    name: str = "ancova"
    outcome: str | None = None
    group: str | None = None
    covariates: list[str] = field(default_factory=list)
    check_assumptions: AncovaAssumptions = field(default_factory=AncovaAssumptions)
    adjusted_means: bool = True
    posthoc: str = "holm"
    effect_size: str = "partial_eta_sq"

    def validate(self) -> None:
        if not self.enabled:
            return
        if self.outcome is None or self.group is None:
            raise ValueError("ancova requires 'outcome' and 'group'.")
        if not self.covariates:
            raise ValueError("ancova requires at least one covariate.")


METHOD_REGISTRY: dict[str, type[MethodConfig]] = {
    "demographic": DemographicConfig,
    "two_group": TwoGroupConfig,
    "paired": PairedConfig,
    "anova_oneway": AnovaOnewayConfig,
    "anova_rm": AnovaRMConfig,
    "anova_mixed": AnovaMixedConfig,
    "correlation": CorrelationConfig,
    "ancova": AncovaConfig,
}


# =============================================================================
# Top-level StudyConfig
# =============================================================================

@dataclass
class StudyConfig:
    """Complete configuration for a single YAML file."""

    study: StudyMetadata
    data: DataConfig
    defaults: Defaults
    output: OutputConfig
    methods: dict[str, MethodConfig]

    def validate(self) -> None:
        for m in self.methods.values():
            m.validate()
        if not any(m.enabled for m in self.methods.values()):
            raise ValueError(
                "No methods are enabled. Set `enabled: true` on at least one "
                "method in the config."
            )

    def enabled_methods(self) -> Iterator[MethodConfig]:
        """Yield enabled method configs in their YAML order."""
        for m in self.methods.values():
            if m.enabled:
                yield m


# =============================================================================
# Loader
# =============================================================================

def _filter_known(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    """Keep only keys that are declared dataclass fields on `cls`.

    Unknown keys trigger a warning rather than a silent TypeError.
    """
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown:
        print(
            f"[pystatkit] Warning: unknown fields in {cls.__name__} config: "
            f"{sorted(unknown)}. These will be ignored."
        )
    return {k: v for k, v in data.items() if k in known}


def load_config(path: str | Path) -> StudyConfig:
    """Load and validate a StudyConfig from YAML."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    study = StudyMetadata(**_filter_known(StudyMetadata, raw.get("study", {})))
    data = DataConfig(**_filter_known(DataConfig, raw.get("data", {})))
    defaults = Defaults(**_filter_known(Defaults, raw.get("defaults", {})))
    output = OutputConfig(**_filter_known(OutputConfig, raw.get("output", {})))

    methods: dict[str, MethodConfig] = {}
    for method_key, method_data in (raw.get("methods") or {}).items():
        if method_key not in METHOD_REGISTRY:
            print(
                f"[pystatkit] Warning: unknown method '{method_key}' in config; "
                f"ignored. Valid methods: {sorted(METHOD_REGISTRY.keys())}"
            )
            continue
        cls = METHOD_REGISTRY[method_key]
        md = dict(method_data or {})
        # Handle ANCOVA's nested assumptions dict.
        if cls is AncovaConfig and "check_assumptions" in md:
            md["check_assumptions"] = AncovaAssumptions(
                **_filter_known(AncovaAssumptions, md["check_assumptions"])
            )
        methods[method_key] = cls(**_filter_known(cls, md))

    cfg = StudyConfig(
        study=study, data=data, defaults=defaults, output=output, methods=methods
    )
    cfg.validate()
    return cfg
