"""One-way comparisons for ≥3 groups: ANOVA with post-hoc, Kruskal-Wallis."""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnalysisConfig
from pystatkit.core.results import AnalysisResult


def _descriptives(df: pd.DataFrame, dv: str, group: str) -> pd.DataFrame:
    """Group-wise descriptives."""
    return df.groupby(group)[dv].agg(
        n="count",
        mean="mean",
        sd="std",
        median="median",
        q1=lambda x: x.quantile(0.25),
        q3=lambda x: x.quantile(0.75),
    )


def _run_posthoc(
    df: pd.DataFrame, config: AnalysisConfig, parametric: bool
) -> pd.DataFrame | None:
    """Run the post-hoc method specified in config."""
    posthoc = config.posthoc
    if posthoc == "none":
        return None

    if posthoc == "tukey":
        if not parametric:
            print(
                "[pystatkit] Note: Tukey's HSD is a parametric post-hoc; "
                "you selected it alongside Kruskal-Wallis. "
                "Dunn's test is usually more appropriate."
            )
        return pg.pairwise_tukey(data=df, dv=config.dv, between=config.group)

    if posthoc == "games_howell":
        return pg.pairwise_gameshowell(
            data=df, dv=config.dv, between=config.group
        )

    if posthoc == "dunn":
        # Dunn's test: pairwise non-parametric with p-value adjustment.
        return pg.pairwise_tests(
            data=df,
            dv=config.dv,
            between=config.group,
            parametric=False,
            padjust="holm",
        )

    return None


def one_way_anova(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """One-way ANOVA with user-specified post-hoc."""
    res = pg.anova(data=df, dv=config.dv, between=config.group, detailed=True)

    # Primary row is the 'between' effect; residual row follows.
    main = res.iloc[0]
    f = float(main["F"])
    df1 = int(main["DF"])
    df2 = int(res.iloc[1]["DF"])
    p = float(main["p_unc"])
    np2 = float(main["np2"])  # partial eta-squared

    posthoc = _run_posthoc(df, config, parametric=True)

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"One-way ANOVA: effect of {config.group} on {config.dv}, "
        f"F({df1}, {df2}) = {f:.2f}, p {p_str}, partial eta-squared = {np2:.3f}."
    )

    return AnalysisResult(
        method="One-way ANOVA",
        method_key="anova",
        primary=res,
        posthoc=posthoc,
        descriptives=_descriptives(df, config.dv, config.group),
        effect_size={"partial_eta_sq": np2},
        n_total=int(df[config.dv].notna().sum()),
        interpretation=interpretation,
        extras={"posthoc_method": config.posthoc},
    )


def kruskal_wallis(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Kruskal-Wallis H test (non-parametric one-way)."""
    res = pg.kruskal(data=df, dv=config.dv, between=config.group)

    h = float(res["H"].iloc[0])
    ddof = int(res["ddof1"].iloc[0])
    p = float(res["p_unc"].iloc[0])

    # For non-parametric, recommend Dunn's unless user specified something else.
    posthoc_config = config.posthoc
    if posthoc_config == "tukey":
        print(
            "[pystatkit] Note: Tukey's HSD is parametric; "
            "using Dunn's test for Kruskal-Wallis post-hoc instead."
        )
        posthoc_config = "dunn"

    # Temporarily swap posthoc for dispatch.
    original = config.posthoc
    config.posthoc = posthoc_config
    posthoc = _run_posthoc(df, config, parametric=False)
    config.posthoc = original

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Kruskal-Wallis H test: effect of {config.group} on {config.dv}, "
        f"H({ddof}) = {h:.2f}, p {p_str}."
    )

    return AnalysisResult(
        method="Kruskal-Wallis H test",
        method_key="kruskal_wallis",
        primary=res,
        posthoc=posthoc,
        descriptives=_descriptives(df, config.dv, config.group),
        effect_size={},
        n_total=int(df[config.dv].notna().sum()),
        interpretation=interpretation,
        extras={"posthoc_method": posthoc_config},
    )
