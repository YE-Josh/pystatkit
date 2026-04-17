"""Assumption checks.

Supports options declared in method configs:
- normality: shapiro | anderson_darling | none
- homogeneity: levene_mean | levene_median | none

Results are presented transparently with clear "OK" / "VIOLATED" / "SKIPPED"
markers. The toolkit never silently switches methods based on outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats as scipy_stats

from pystatkit.core.config import (
    AnovaOnewayConfig,
    MethodConfig,
    PairedConfig,
    TwoGroupConfig,
)


@dataclass
class AssumptionReport:
    """Structured output of assumption checks."""

    normality: pd.DataFrame | None = None
    homogeneity: pd.DataFrame | None = None
    notes: list[str] = field(default_factory=list)

    def to_text(self, alpha: float = 0.05) -> str:
        lines = ["=== Assumption Checks ==="]

        if self.normality is not None and not self.normality.empty:
            lines.append("\nNormality:")
            for idx, row in self.normality.iterrows():
                status = "OK" if row["pval"] >= alpha else "VIOLATED"
                stat_name = row.get("stat_name", "stat")
                stat_val = row.get("stat", float("nan"))
                lines.append(
                    f"  {idx!s:<24} {stat_name} = {stat_val:.3f}, "
                    f"p = {row['pval']:.4f}  [{status}]"
                )

        if self.homogeneity is not None and not self.homogeneity.empty:
            lines.append("\nHomogeneity of variance:")
            for _, row in self.homogeneity.iterrows():
                status = "OK" if row["pval"] >= alpha else "VIOLATED"
                lines.append(
                    f"  {row['method']:<24} W = {row['W']:.3f}, "
                    f"p = {row['pval']:.4f}  [{status}]"
                )

        if self.notes:
            lines.append("\nNotes:")
            for note in self.notes:
                lines.append(f"  - {note}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Normality
# ---------------------------------------------------------------------------

def _shapiro_by_group(df: pd.DataFrame, dv: str, group: str) -> pd.DataFrame:
    """Shapiro-Wilk per group level."""
    rows = []
    for level, sub in df.groupby(group):
        values = sub[dv].dropna().to_numpy()
        if len(values) < 3:
            rows.append({"stat_name": "W", "stat": np.nan, "pval": np.nan})
            continue
        w, p = scipy_stats.shapiro(values)
        rows.append({"stat_name": "W", "stat": float(w), "pval": float(p)})
    idx = sorted(df[group].dropna().unique())
    return pd.DataFrame(rows, index=idx)


def _anderson_darling_by_group(
    df: pd.DataFrame, dv: str, group: str
) -> pd.DataFrame:
    """Anderson-Darling per group. Reports test statistic and approximate p-value."""
    rows = []
    for level, sub in df.groupby(group):
        values = sub[dv].dropna().to_numpy()
        if len(values) < 8:
            rows.append({"stat_name": "A²", "stat": np.nan, "pval": np.nan})
            continue
        result = scipy_stats.anderson(values, dist="norm")
        # Approximate p from critical values: find smallest α where A² exceeds critical.
        sig_levels = result.significance_level / 100  # e.g. [25, 10, 5, 2.5, 1] -> /100
        crit = result.critical_values
        p_approx = 1.0
        for s, c in zip(sig_levels, crit):
            if result.statistic >= c:
                p_approx = s
        rows.append(
            {"stat_name": "A²", "stat": float(result.statistic), "pval": float(p_approx)}
        )
    idx = sorted(df[group].dropna().unique())
    return pd.DataFrame(rows, index=idx)


def _shapiro_on_differences(
    df: pd.DataFrame, dv: str, subject: str, condition: str
) -> pd.DataFrame:
    """Shapiro-Wilk on within-subject differences (for paired designs)."""
    wide = df.pivot_table(index=subject, columns=condition, values=dv).dropna()
    if wide.shape[1] != 2:
        raise ValueError(
            f"Expected exactly 2 conditions, found {wide.shape[1]}: {list(wide.columns)}"
        )
    diffs = (wide.iloc[:, 0] - wide.iloc[:, 1]).to_numpy()
    if len(diffs) < 3:
        return pd.DataFrame(
            [{"stat_name": "W", "stat": np.nan, "pval": np.nan}], index=["differences"]
        )
    w, p = scipy_stats.shapiro(diffs)
    return pd.DataFrame(
        [{"stat_name": "W", "stat": float(w), "pval": float(p)}], index=["differences"]
    )


def _run_normality(
    method_name: str,
    df: pd.DataFrame,
    dv: str,
    group: str | None = None,
    subject: str | None = None,
    condition: str | None = None,
) -> pd.DataFrame | None:
    """Dispatch on the normality method name."""
    if method_name == "none":
        return None
    if subject and condition:  # paired
        if method_name == "shapiro":
            return _shapiro_on_differences(df, dv, subject, condition)
        # anderson-darling on differences (rarely needed; reuse shapiro helper)
        if method_name == "anderson_darling":
            wide = df.pivot_table(index=subject, columns=condition, values=dv).dropna()
            diffs = (wide.iloc[:, 0] - wide.iloc[:, 1]).to_numpy()
            if len(diffs) < 8:
                return pd.DataFrame(
                    [{"stat_name": "A²", "stat": np.nan, "pval": np.nan}],
                    index=["differences"],
                )
            r = scipy_stats.anderson(diffs, dist="norm")
            p_approx = 1.0
            for s, c in zip(r.significance_level / 100, r.critical_values):
                if r.statistic >= c:
                    p_approx = s
            return pd.DataFrame(
                [{"stat_name": "A²", "stat": float(r.statistic), "pval": float(p_approx)}],
                index=["differences"],
            )
    if group:
        if method_name == "shapiro":
            return _shapiro_by_group(df, dv, group)
        if method_name == "anderson_darling":
            return _anderson_darling_by_group(df, dv, group)
    raise ValueError(f"Unknown normality check: '{method_name}'")


# ---------------------------------------------------------------------------
# Homogeneity of variance
# ---------------------------------------------------------------------------

def _levene(df: pd.DataFrame, dv: str, group: str, center: str) -> pd.DataFrame:
    """Levene's test with specified centering (mean or median).

    Median-centered Levene (Brown-Forsythe) is robust to non-normality and
    is the recommended default.
    """
    groups = [sub[dv].dropna().to_numpy() for _, sub in df.groupby(group)]
    w, p = scipy_stats.levene(*groups, center=center)
    label = "Levene (mean)" if center == "mean" else "Levene (median)"
    return pd.DataFrame(
        [{"method": label, "W": float(w), "pval": float(p)}]
    )


def _run_homogeneity(
    method_name: str, df: pd.DataFrame, dv: str, group: str
) -> pd.DataFrame | None:
    if method_name == "none":
        return None
    if method_name == "levene_mean":
        return _levene(df, dv, group, center="mean")
    if method_name == "levene_median":
        return _levene(df, dv, group, center="median")
    raise ValueError(f"Unknown homogeneity check: '{method_name}'")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_assumption_checks(
    df: pd.DataFrame, method_cfg: MethodConfig, id_col: str
) -> AssumptionReport:
    """Run assumption checks appropriate for the given method config."""
    report = AssumptionReport()

    if isinstance(method_cfg, TwoGroupConfig):
        df_valid = df[df[method_cfg.outcome].notna()]
        report.normality = _run_normality(
            method_cfg.normality_check,
            df_valid,
            dv=method_cfg.outcome,
            group=method_cfg.group,
        )
        report.homogeneity = _run_homogeneity(
            method_cfg.homogeneity_check,
            df_valid,
            dv=method_cfg.outcome,
            group=method_cfg.group,
        )
        _add_two_group_notes(report, method_cfg)

    elif isinstance(method_cfg, PairedConfig):
        subject = method_cfg.id or id_col
        df_valid = df[df[method_cfg.outcome].notna()]
        report.normality = _run_normality(
            method_cfg.normality_check,
            df_valid,
            dv=method_cfg.outcome,
            subject=subject,
            condition=method_cfg.condition,
        )
        _add_paired_notes(report, method_cfg)

    elif isinstance(method_cfg, AnovaOnewayConfig):
        df_valid = df[df[method_cfg.outcome].notna()]
        report.normality = _run_normality(
            method_cfg.normality_check,
            df_valid,
            dv=method_cfg.outcome,
            group=method_cfg.group,
        )
        report.homogeneity = _run_homogeneity(
            method_cfg.homogeneity_check,
            df_valid,
            dv=method_cfg.outcome,
            group=method_cfg.group,
        )
        _add_oneway_notes(report, method_cfg)

    return report


def _add_two_group_notes(report: AssumptionReport, cfg: TwoGroupConfig) -> None:
    if report.homogeneity is not None and not report.homogeneity.empty:
        p_lev = report.homogeneity["pval"].iloc[0]
        if pd.notna(p_lev) and p_lev < 0.05:
            report.notes.append(
                "Unequal variances: Welch's t-test is more robust than Student's t-test."
            )
    if report.normality is not None and (report.normality["pval"] < 0.05).any():
        report.notes.append(
            "Normality violated in ≥1 group: Mann-Whitney U is a non-parametric "
            "alternative. (For n > 30 per group, t-tests are fairly robust.)"
        )


def _add_paired_notes(report: AssumptionReport, cfg: PairedConfig) -> None:
    if report.normality is not None and (report.normality["pval"] < 0.05).any():
        report.notes.append(
            "Normality of within-subject differences violated: consider Wilcoxon "
            "signed-rank."
        )


def _add_oneway_notes(report: AssumptionReport, cfg: AnovaOnewayConfig) -> None:
    if report.homogeneity is not None and not report.homogeneity.empty:
        p_lev = report.homogeneity["pval"].iloc[0]
        if pd.notna(p_lev) and p_lev < 0.05:
            report.notes.append(
                "Unequal variances: consider Welch's ANOVA or Games-Howell post-hoc."
            )
    if report.normality is not None and (report.normality["pval"] < 0.05).any():
        report.notes.append(
            "Normality violated in ≥1 group: consider Kruskal-Wallis."
        )
