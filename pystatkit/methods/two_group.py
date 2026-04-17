"""Two-group independent comparisons: Student's t, Welch's t, Mann-Whitney U."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnalysisConfig
from pystatkit.core.results import AnalysisResult


def _descriptives(df: pd.DataFrame, dv: str, group: str) -> pd.DataFrame:
    """Group-wise mean, SD, median, IQR, n."""
    agg = df.groupby(group)[dv].agg(
        n="count",
        mean="mean",
        sd="std",
        median="median",
        q1=lambda x: x.quantile(0.25),
        q3=lambda x: x.quantile(0.75),
    )
    return agg


def _get_two_samples(
    df: pd.DataFrame, dv: str, group: str
) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Extract two group arrays and their labels, sorted for reproducibility."""
    levels = sorted(df[group].dropna().unique())
    if len(levels) != 2:
        raise ValueError(
            f"Expected exactly 2 groups in '{group}', found {len(levels)}: {levels}"
        )
    g1, g2 = levels
    x = df.loc[df[group] == g1, dv].dropna().to_numpy()
    y = df.loc[df[group] == g2, dv].dropna().to_numpy()
    return x, y, str(g1), str(g2)


def _ttest(df: pd.DataFrame, config: AnalysisConfig, welch: bool) -> AnalysisResult:
    """Shared implementation for Student's and Welch's t-tests."""
    x, y, g1, g2 = _get_two_samples(df, config.dv, config.group)
    res = pg.ttest(x, y, paired=False, correction=welch)

    method_name = "Welch's t-test" if welch else "Independent t-test"
    method_key = "welch_t" if welch else "independent_t"

    t = float(res["T"].iloc[0])
    dof = float(res["dof"].iloc[0])
    p = float(res["p_val"].iloc[0])
    d = float(res["cohen_d"].iloc[0])
    ci_lo, ci_hi = res["CI95"].iloc[0]

    # APA-style interpretation sentence.
    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    dof_str = f"{dof:.2f}" if welch else f"{int(round(dof))}"
    interpretation = (
        f"{method_name}: {config.dv} differed between {g1} and {g2}, "
        f"t({dof_str}) = {t:.2f}, p {p_str}, Cohen's d = {d:.2f} "
        f"[95% CI: {ci_lo:.2f}, {ci_hi:.2f}]."
    )

    return AnalysisResult(
        method=method_name,
        method_key=method_key,
        primary=res,
        descriptives=_descriptives(df, config.dv, config.group),
        effect_size={"cohen_d": d},
        n_total=len(x) + len(y),
        interpretation=interpretation,
        extras={"group_labels": [g1, g2], "welch_correction": welch},
    )


def independent_t(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Student's independent samples t-test (assumes equal variances)."""
    return _ttest(df, config, welch=False)


def welch_t(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Welch's t-test (does not assume equal variances)."""
    return _ttest(df, config, welch=True)


def mann_whitney(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Mann-Whitney U test (non-parametric two-group comparison)."""
    x, y, g1, g2 = _get_two_samples(df, config.dv, config.group)
    res = pg.mwu(x, y, alternative="two-sided")

    u = float(res["U_val"].iloc[0])
    p = float(res["p_val"].iloc[0])
    rbc = float(res["RBC"].iloc[0])  # rank-biserial correlation as effect size

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Mann-Whitney U test: {config.dv} differed between {g1} and {g2}, "
        f"U = {u:.1f}, p {p_str}, rank-biserial r = {rbc:.2f}."
    )

    return AnalysisResult(
        method="Mann-Whitney U test",
        method_key="mann_whitney",
        primary=res,
        descriptives=_descriptives(df, config.dv, config.group),
        effect_size={"rank_biserial": rbc},
        n_total=len(x) + len(y),
        interpretation=interpretation,
        extras={"group_labels": [g1, g2]},
    )
