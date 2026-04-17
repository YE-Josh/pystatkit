"""Two-group independent comparisons: Student's t, Welch's t, Mann-Whitney U."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pingouin as pg

from pystatkit.core.config import TwoGroupConfig
from pystatkit.core.data_loader import filter_dv
from pystatkit.core.results import AnalysisResult


def _descriptives(df: pd.DataFrame, dv: str, group: str) -> pd.DataFrame:
    return df.groupby(group)[dv].agg(
        n="count",
        mean="mean",
        sd="std",
        median="median",
        q1=lambda x: x.quantile(0.25),
        q3=lambda x: x.quantile(0.75),
    )


def _get_two_samples(
    df: pd.DataFrame, dv: str, group: str
) -> tuple[np.ndarray, np.ndarray, str, str]:
    levels = sorted(df[group].dropna().unique())
    if len(levels) != 2:
        raise ValueError(
            f"Expected exactly 2 groups in '{group}', found {len(levels)}: {levels}"
        )
    g1, g2 = levels
    x = df.loc[df[group] == g1, dv].dropna().to_numpy()
    y = df.loc[df[group] == g2, dv].dropna().to_numpy()
    return x, y, str(g1), str(g2)


def _ttest(df: pd.DataFrame, cfg: TwoGroupConfig, welch: bool) -> AnalysisResult:
    df = filter_dv(df, cfg.outcome)
    x, y, g1, g2 = _get_two_samples(df, cfg.outcome, cfg.group)

    alt_map = {"two_sided": "two-sided", "greater": "greater", "less": "less"}
    alt = alt_map[cfg.alternative]

    res = pg.ttest(x, y, paired=False, correction=welch, alternative=alt)

    method_name = "Welch's t-test" if welch else "Independent t-test"
    method_key = "welch_t" if welch else "independent_t"

    t = float(res["T"].iloc[0])
    dof = float(res["dof"].iloc[0])
    p = float(res["p_val"].iloc[0])
    d = float(res["cohen_d"].iloc[0])
    ci_lo, ci_hi = res["CI95"].iloc[0]

    # If requested effect size is hedges_g, convert from cohen_d.
    reported_es: dict[str, float]
    if cfg.effect_size == "hedges_g":
        n1, n2 = len(x), len(y)
        df_total = n1 + n2 - 2
        # Hedges correction factor.
        j = 1 - 3 / (4 * df_total - 1) if df_total > 1 else 1.0
        g = d * j
        reported_es = {"hedges_g": float(g)}
        es_str = f"Hedges' g = {g:.2f}"
    else:
        reported_es = {"cohens_d": d}
        es_str = f"Cohen's d = {d:.2f}"

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    dof_str = f"{dof:.2f}" if welch else f"{int(round(dof))}"
    interpretation = (
        f"{method_name}: {cfg.outcome} differed between {g1} and {g2}, "
        f"t({dof_str}) = {t:.2f}, p {p_str}, {es_str} "
        f"[95% CI: {ci_lo:.2f}, {ci_hi:.2f}]."
    )

    return AnalysisResult(
        method=method_name,
        method_key=method_key,
        primary=res,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size=reported_es,
        n_total=len(x) + len(y),
        interpretation=interpretation,
        extras={
            "group_labels": [g1, g2],
            "welch_correction": welch,
            "alternative": cfg.alternative,
        },
    )


def independent_t(df: pd.DataFrame, cfg: TwoGroupConfig) -> AnalysisResult:
    return _ttest(df, cfg, welch=False)


def welch_t(df: pd.DataFrame, cfg: TwoGroupConfig) -> AnalysisResult:
    return _ttest(df, cfg, welch=True)


def mann_whitney(df: pd.DataFrame, cfg: TwoGroupConfig) -> AnalysisResult:
    df = filter_dv(df, cfg.outcome)
    x, y, g1, g2 = _get_two_samples(df, cfg.outcome, cfg.group)

    alt_map = {"two_sided": "two-sided", "greater": "greater", "less": "less"}
    res = pg.mwu(x, y, alternative=alt_map[cfg.alternative])

    u = float(res["U_val"].iloc[0])
    p = float(res["p_val"].iloc[0])
    rbc = float(res["RBC"].iloc[0])

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Mann-Whitney U test: {cfg.outcome} differed between {g1} and {g2}, "
        f"U = {u:.1f}, p {p_str}, rank-biserial r = {rbc:.2f}."
    )

    return AnalysisResult(
        method="Mann-Whitney U test",
        method_key="mann_whitney",
        primary=res,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size={"rank_biserial": rbc},
        n_total=len(x) + len(y),
        interpretation=interpretation,
        extras={"group_labels": [g1, g2], "alternative": cfg.alternative},
    )
