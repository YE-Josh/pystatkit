"""One-way comparisons for ≥3 groups: ANOVA, Welch's ANOVA, Kruskal-Wallis."""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnovaOnewayConfig
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


def _posthoc_parametric(
    df: pd.DataFrame, cfg: AnovaOnewayConfig
) -> pd.DataFrame | None:
    """Post-hoc for classic/Welch ANOVA."""
    if cfg.posthoc == "none":
        return None
    if cfg.posthoc == "tukey":
        return pg.pairwise_tukey(data=df, dv=cfg.outcome, between=cfg.group)
    if cfg.posthoc == "games_howell":
        return pg.pairwise_gameshowell(data=df, dv=cfg.outcome, between=cfg.group)
    if cfg.posthoc == "dunn":
        print("[pystatkit] Note: Dunn's is for non-parametric tests; "
              "using Games-Howell for ANOVA instead.")
        return pg.pairwise_gameshowell(data=df, dv=cfg.outcome, between=cfg.group)
    return None


def _posthoc_nonparametric(
    df: pd.DataFrame, cfg: AnovaOnewayConfig
) -> pd.DataFrame | None:
    """Post-hoc for Kruskal-Wallis: default to Dunn's."""
    if cfg.posthoc == "none":
        return None
    # Override non-parametric with Dunn regardless of user selection if they
    # picked a parametric post-hoc by mistake — but tell them.
    if cfg.posthoc in ("tukey", "games_howell"):
        print(f"[pystatkit] Note: '{cfg.posthoc}' is parametric; "
              f"using Dunn's for Kruskal-Wallis instead.")
    return pg.pairwise_tests(
        data=df,
        dv=cfg.outcome,
        between=cfg.group,
        parametric=False,
        padjust="holm",
    )


def one_way_anova(
    df: pd.DataFrame, cfg: AnovaOnewayConfig
) -> AnalysisResult:
    """Classic (Fisher) one-way ANOVA."""
    df = filter_dv(df, cfg.outcome)
    res = pg.anova(data=df, dv=cfg.outcome, between=cfg.group, detailed=True)

    main = res.iloc[0]
    f = float(main["F"])
    df1 = int(main["DF"])
    df2 = int(res.iloc[1]["DF"])
    p = float(main["p_unc"])
    np2 = float(main["np2"])

    posthoc = _posthoc_parametric(df, cfg)

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"One-way ANOVA: effect of {cfg.group} on {cfg.outcome}, "
        f"F({df1}, {df2}) = {f:.2f}, p {p_str}, partial eta-squared = {np2:.3f}."
    )

    return AnalysisResult(
        method="One-way ANOVA",
        method_key="anova",
        primary=res,
        posthoc=posthoc,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size={"partial_eta_sq": np2},
        n_total=int(df[cfg.outcome].notna().sum()),
        interpretation=interpretation,
        extras={"posthoc_method": cfg.posthoc},
    )


def welch_anova(
    df: pd.DataFrame, cfg: AnovaOnewayConfig
) -> AnalysisResult:
    """Welch's ANOVA: robust to unequal variances."""
    df = filter_dv(df, cfg.outcome)
    res = pg.welch_anova(data=df, dv=cfg.outcome, between=cfg.group)

    main = res.iloc[0]
    f = float(main["F"])
    df1 = float(main["ddof1"])
    df2 = float(main["ddof2"])
    p = float(main["p_unc"])
    np2 = float(main["np2"])

    # Games-Howell is the recommended post-hoc for Welch's ANOVA.
    posthoc_cfg = cfg
    if cfg.posthoc == "tukey":
        print("[pystatkit] Note: Tukey assumes equal variances; "
              "using Games-Howell for Welch's ANOVA instead.")
    posthoc = None
    if cfg.posthoc != "none":
        posthoc = pg.pairwise_gameshowell(data=df, dv=cfg.outcome, between=cfg.group)

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Welch's ANOVA: effect of {cfg.group} on {cfg.outcome}, "
        f"F({df1:.2f}, {df2:.2f}) = {f:.2f}, p {p_str}, "
        f"partial eta-squared = {np2:.3f}."
    )

    return AnalysisResult(
        method="Welch's ANOVA",
        method_key="welch_anova",
        primary=res,
        posthoc=posthoc,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size={"partial_eta_sq": np2},
        n_total=int(df[cfg.outcome].notna().sum()),
        interpretation=interpretation,
        extras={"posthoc_method": "games_howell"},
    )


def kruskal_wallis(
    df: pd.DataFrame, cfg: AnovaOnewayConfig
) -> AnalysisResult:
    """Kruskal-Wallis H test (non-parametric)."""
    df = filter_dv(df, cfg.outcome)
    res = pg.kruskal(data=df, dv=cfg.outcome, between=cfg.group)

    h = float(res["H"].iloc[0])
    ddof = int(res["ddof1"].iloc[0])
    p = float(res["p_unc"].iloc[0])

    posthoc = _posthoc_nonparametric(df, cfg)

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Kruskal-Wallis H test: effect of {cfg.group} on {cfg.outcome}, "
        f"H({ddof}) = {h:.2f}, p {p_str}."
    )

    return AnalysisResult(
        method="Kruskal-Wallis H test",
        method_key="kruskal_wallis",
        primary=res,
        posthoc=posthoc,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size={},
        n_total=int(df[cfg.outcome].notna().sum()),
        interpretation=interpretation,
        extras={"posthoc_method": "dunn" if cfg.posthoc != "none" else "none"},
    )
