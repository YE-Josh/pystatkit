"""Paired (within-subject) two-condition comparisons: paired t-test, Wilcoxon."""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnalysisConfig
from pystatkit.core.results import AnalysisResult


def _to_wide(
    df: pd.DataFrame, dv: str, subject: str, condition: str
) -> pd.DataFrame:
    """Pivot long-format data to subject × condition, dropping rows with missing pairs."""
    wide = df.pivot_table(index=subject, columns=condition, values=dv)
    if wide.shape[1] != 2:
        raise ValueError(
            f"Paired design requires exactly 2 conditions, "
            f"found {wide.shape[1]}: {list(wide.columns)}"
        )
    before_drop = len(wide)
    wide = wide.dropna()
    n_dropped = before_drop - len(wide)
    if n_dropped > 0:
        print(
            f"[pystatkit] Note: dropped {n_dropped} subject(s) with incomplete pairs."
        )
    return wide


def _descriptives_paired(wide: pd.DataFrame) -> pd.DataFrame:
    """Mean, SD, median, n for each condition; plus difference."""
    desc = wide.agg(["count", "mean", "std", "median"]).T
    desc.columns = ["n", "mean", "sd", "median"]
    diff = wide.iloc[:, 0] - wide.iloc[:, 1]
    desc.loc["difference"] = [
        len(diff),
        diff.mean(),
        diff.std(),
        diff.median(),
    ]
    return desc


def paired_t(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Paired-samples t-test."""
    wide = _to_wide(df, config.dv, config.subject, config.condition)
    c1, c2 = wide.columns[0], wide.columns[1]
    res = pg.ttest(wide[c1], wide[c2], paired=True)

    t = float(res["T"].iloc[0])
    dof = int(res["dof"].iloc[0])
    p = float(res["p_val"].iloc[0])
    d = float(res["cohen_d"].iloc[0])
    ci_lo, ci_hi = res["CI95"].iloc[0]

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Paired t-test: {config.dv} differed between {c1} and {c2}, "
        f"t({dof}) = {t:.2f}, p {p_str}, Cohen's d = {d:.2f} "
        f"[95% CI: {ci_lo:.2f}, {ci_hi:.2f}]."
    )

    return AnalysisResult(
        method="Paired t-test",
        method_key="paired_t",
        primary=res,
        descriptives=_descriptives_paired(wide),
        effect_size={"cohen_d": d},
        n_total=len(wide),
        interpretation=interpretation,
        extras={"condition_labels": [str(c1), str(c2)]},
    )


def wilcoxon(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Wilcoxon signed-rank test (non-parametric paired comparison)."""
    wide = _to_wide(df, config.dv, config.subject, config.condition)
    c1, c2 = wide.columns[0], wide.columns[1]
    res = pg.wilcoxon(wide[c1], wide[c2], alternative="two-sided")

    w = float(res["W_val"].iloc[0])
    p = float(res["p_val"].iloc[0])
    rbc = float(res["RBC"].iloc[0])  # matched-pairs rank-biserial

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Wilcoxon signed-rank test: {config.dv} differed between {c1} and {c2}, "
        f"W = {w:.1f}, p {p_str}, matched-pairs rank-biserial r = {rbc:.2f}."
    )

    return AnalysisResult(
        method="Wilcoxon signed-rank test",
        method_key="wilcoxon",
        primary=res,
        descriptives=_descriptives_paired(wide),
        effect_size={"rank_biserial": rbc},
        n_total=len(wide),
        interpretation=interpretation,
        extras={"condition_labels": [str(c1), str(c2)]},
    )
