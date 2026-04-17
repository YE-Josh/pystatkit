"""Repeated-measures ANOVA (one or more within-subject factors).

Uses pingouin's rm_anova with correction=True, which returns Mauchly's test
of sphericity and Greenhouse-Geisser corrected p-values in the same table.
For multi-factor within designs, pingouin returns a row per main effect
and interaction.
"""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnovaRMConfig
from pystatkit.core.data_loader import filter_dv
from pystatkit.core.results import AnalysisResult


def _descriptives_by_within(
    df: pd.DataFrame, dv: str, within: list[str]
) -> pd.DataFrame:
    """Mean, SD, n per cell of the within-subject factor(s)."""
    return df.groupby(within, observed=True)[dv].agg(
        n="count", mean="mean", sd="std", median="median"
    )


def _format_interpretation(
    primary: pd.DataFrame, outcome: str, correction: str
) -> str:
    """Build APA-style sentence(s) for each within-subject effect."""
    sentences = []
    # Drop the Error rows (those with NaN in the F column).
    effect_rows = primary[primary["F"].notna()]

    for _, row in effect_rows.iterrows():
        source = row["Source"]
        f = row["F"]
        df1 = row["DF"]
        np2 = row.get("np2", row.get("ng2", float("nan")))

        # Pick the right p-value: GG/HF corrected if sphericity violated, else uncorrected.
        use_corrected = (
            correction != "none"
            and "sphericity" in row
            and row["sphericity"] is False
        )
        p_col = f"p_{correction.upper()}_corr" if use_corrected else "p_unc"
        p = row.get(p_col, row.get("p_unc"))

        # DF reporting: if corrected, multiply by epsilon for reported df (APA convention).
        if use_corrected and "eps" in row and pd.notna(row["eps"]):
            eps = row["eps"]
            df1_str = f"{df1 * eps:.2f}"
            note = f" ({correction.upper()}-corrected)"
        else:
            df1_str = f"{int(df1)}"
            note = ""

        p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
        np2_str = f"{np2:.3f}" if pd.notna(np2) else "n/a"

        sentences.append(
            f"Effect of {source} on {outcome}{note}: "
            f"F({df1_str}) = {f:.2f}, p {p_str}, partial eta-squared = {np2_str}."
        )
    return " ".join(sentences)


def rm_anova(df: pd.DataFrame, cfg: AnovaRMConfig, id_col: str) -> AnalysisResult:
    """Repeated-measures ANOVA with Mauchly's test and GG/HF correction."""
    df = filter_dv(df, cfg.outcome)
    subject = cfg.id or id_col

    # pingouin accepts a single string or a list for `within`.
    within_arg = cfg.within[0] if len(cfg.within) == 1 else list(cfg.within)

    # correction=True enables Mauchly's test + GG columns in output.
    want_correction = cfg.sphericity_correction != "none"
    primary = pg.rm_anova(
        data=df,
        dv=cfg.outcome,
        within=within_arg,
        subject=subject,
        detailed=True,
        correction=want_correction,
        effsize="np2",
    )

    # Post-hoc pairwise comparisons.
    posthoc = None
    if cfg.posthoc != "none":
        padjust = cfg.posthoc  # "holm" / "bonferroni" map directly
        if padjust not in ("holm", "bonferroni", "fdr_bh"):
            padjust = "holm"
        posthoc = pg.pairwise_tests(
            data=df,
            dv=cfg.outcome,
            within=within_arg,
            subject=subject,
            padjust=padjust,
        )

    # Collect effect size(s) into a dict keyed by effect name.
    es: dict[str, float] = {}
    effect_rows = primary[primary["F"].notna()] if "F" in primary.columns else primary
    for _, row in effect_rows.iterrows():
        np2 = row.get("np2", row.get("ng2"))
        if pd.notna(np2):
            es[f"{row['Source']}_partial_eta_sq"] = float(np2)

    interpretation = _format_interpretation(
        primary, cfg.outcome, cfg.sphericity_correction
    )

    # Descriptive table: cell means across within-subject levels.
    within_cols = cfg.within if len(cfg.within) > 1 else cfg.within
    descriptives = _descriptives_by_within(df, cfg.outcome, within_cols)

    # Sphericity diagnostics — extract into extras.
    sph_info = {}
    if "sphericity" in primary.columns:
        effect_row = effect_rows.iloc[0] if len(effect_rows) else None
        if effect_row is not None:
            sph_info = {
                "mauchly_W": effect_row.get("W_spher"),
                "mauchly_p": effect_row.get("p_spher"),
                "sphericity_ok": effect_row.get("sphericity"),
                "epsilon_gg": effect_row.get("eps"),
            }

    return AnalysisResult(
        method="Repeated-measures ANOVA",
        method_key="anova_rm",
        primary=primary,
        posthoc=posthoc,
        descriptives=descriptives,
        effect_size=es,
        n_total=int(df[subject].nunique()),
        interpretation=interpretation,
        extras={
            "within": list(cfg.within),
            "sphericity_correction": cfg.sphericity_correction,
            "sphericity": sph_info,
            "posthoc_method": cfg.posthoc,
        },
    )
