"""Unified result container for statistical analyses.

All methods (t-tests, ANOVA, non-parametric) return an AnalysisResult
to allow consistent formatting and output downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class AnalysisResult:
    """Container for the output of a single statistical analysis.

    Attributes
    ----------
    method : str
        Human-readable method name (e.g. "Welch's t-test").
    method_key : str
        Machine key matching the config (e.g. "welch_t").
    primary : pd.DataFrame
        The main result table (one or more rows; columns depend on method).
    posthoc : pd.DataFrame | None
        Pairwise comparisons, if applicable.
    descriptives : pd.DataFrame | None
        Group-wise mean, SD, n, etc. — used in APA tables.
    effect_size : dict[str, float]
        Effect size(s) with name as key. E.g. {"cohen_d": 0.52}.
    n_total : int
        Total sample size used in the analysis.
    interpretation : str
        Auto-generated APA-style sentence summarizing the result.
    extras : dict
        Method-specific extra information (e.g. assumption corrections applied).
    """

    method: str
    method_key: str
    primary: pd.DataFrame
    posthoc: pd.DataFrame | None = None
    descriptives: pd.DataFrame | None = None
    effect_size: dict[str, float] = field(default_factory=dict)
    n_total: int = 0
    interpretation: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Short human-readable summary of the result."""
        lines = [f"Method: {self.method}", f"n = {self.n_total}"]
        if self.interpretation:
            lines.append(self.interpretation)
        return "\n".join(lines)
