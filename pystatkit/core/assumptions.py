"""Assumption checks: normality (Shapiro-Wilk) and homogeneity of variance (Levene).

Results are reported transparently to the user. The toolkit never silently
switches methods based on assumption outcomes — the researcher decides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnalysisConfig


def _drop_dv_na(df: pd.DataFrame, dv: str) -> pd.DataFrame:
    """Return rows with a non-null DV. Used before any test to avoid NaN-induced failures."""
    return df[df[dv].notna()].copy()


@dataclass
class AssumptionReport:
    """Structured output of assumption checks for a given design."""

    normality: pd.DataFrame | None = None
    homogeneity: pd.DataFrame | None = None
    notes: list[str] = field(default_factory=list)

    def any_violation(self, alpha: float = 0.05) -> bool:
        """Return True if any assumption test has p < alpha."""
        violated = False
        if self.normality is not None and "pval" in self.normality.columns:
            if (self.normality["pval"] < alpha).any():
                violated = True
        if self.homogeneity is not None and "pval" in self.homogeneity.columns:
            if (self.homogeneity["pval"] < alpha).any():
                violated = True
        return violated

    def to_text(self, alpha: float = 0.05) -> str:
        """Human-readable summary for printing to the console."""
        lines = ["=== Assumption Checks ==="]

        if self.normality is not None:
            lines.append("\nNormality (Shapiro–Wilk):")
            for idx, row in self.normality.iterrows():
                status = "OK" if row["pval"] >= alpha else "VIOLATED"
                lines.append(
                    f"  {idx!s:<20} W = {row['W']:.3f}, p = {row['pval']:.4f}  [{status}]"
                )

        if self.homogeneity is not None:
            lines.append("\nHomogeneity of variance (Levene):")
            for _, row in self.homogeneity.iterrows():
                status = "OK" if row["pval"] >= alpha else "VIOLATED"
                stat_name = "W" if "W" in row else "F"
                stat_val = row.get("W", row.get("F"))
                lines.append(
                    f"  {stat_name} = {stat_val:.3f}, p = {row['pval']:.4f}  [{status}]"
                )

        if self.notes:
            lines.append("\nNotes:")
            for note in self.notes:
                lines.append(f"  - {note}")

        return "\n".join(lines)


def _check_normality_grouped(
    df: pd.DataFrame, dv: str, group: str
) -> pd.DataFrame:
    """Shapiro-Wilk test for each level of `group`."""
    return pg.normality(data=df, dv=dv, group=group)


def _check_normality_paired_differences(
    df: pd.DataFrame, dv: str, subject: str, condition: str
) -> pd.DataFrame:
    """For paired designs, test normality of the within-subject differences."""
    wide = df.pivot_table(index=subject, columns=condition, values=dv)
    if wide.shape[1] != 2:
        raise ValueError(
            f"Expected exactly 2 conditions, found {wide.shape[1]}: {list(wide.columns)}"
        )
    diffs = wide.iloc[:, 0] - wide.iloc[:, 1]
    result = pg.normality(diffs.dropna())
    # Normalise output format to match grouped case.
    result.index = ["differences"]
    return result


def _check_homogeneity(df: pd.DataFrame, dv: str, group: str) -> pd.DataFrame:
    """Levene's test for homogeneity of variance across groups."""
    return pg.homoscedasticity(data=df, dv=dv, group=group, method="levene")


def run_assumption_checks(
    df: pd.DataFrame, config: AnalysisConfig
) -> AssumptionReport:
    """Run assumption checks appropriate to the design in `config`.

    Parameters
    ----------
    df : pd.DataFrame
        Input data in long format.
    config : AnalysisConfig
        The analysis configuration (used to determine design and columns).

    Returns
    -------
    AssumptionReport
        Structured results including notes about implications.
    """
    report = AssumptionReport()

    # Filter to rows with a valid DV so tests don't receive NaN-padded groups.
    df = _drop_dv_na(df, config.dv)

    if config.design == "two_group_independent":
        report.normality = _check_normality_grouped(df, config.dv, config.group)
        report.homogeneity = _check_homogeneity(df, config.dv, config.group)
        equal_var = report.homogeneity["equal_var"].iloc[0]
        if equal_var is False:  # explicit False, not NaN
            report.notes.append(
                "Unequal variances detected: Welch's t-test is more robust "
                "than Student's t-test."
            )
        if not report.normality["normal"].all():
            report.notes.append(
                "Normality violated in at least one group: consider Mann-Whitney U. "
                "Note: for n > 30 per group, t-tests are fairly robust to mild violations."
            )

    elif config.design == "two_group_paired":
        report.normality = _check_normality_paired_differences(
            df, config.dv, config.subject, config.condition
        )
        if not report.normality["normal"].iloc[0]:
            report.notes.append(
                "Normality of within-subject differences violated: "
                "consider Wilcoxon signed-rank test."
            )

    elif config.design == "one_way_anova":
        report.normality = _check_normality_grouped(df, config.dv, config.group)
        report.homogeneity = _check_homogeneity(df, config.dv, config.group)
        equal_var = report.homogeneity["equal_var"].iloc[0]
        if equal_var is False:
            report.notes.append(
                "Unequal variances: consider Welch's ANOVA or Games-Howell post-hoc."
            )
        if not report.normality["normal"].all():
            report.notes.append(
                "Normality violated in at least one group: "
                "consider Kruskal-Wallis as a non-parametric alternative."
            )

    return report
