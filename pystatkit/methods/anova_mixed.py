"""Mixed ANOVA: one within-subject factor × one between-subject factor.

Pingouin's mixed_anova returns three rows: the between effect, the within
effect, and their interaction. When the interaction is significant, we follow
up with simple effects (within effect at each level of between).
"""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import AnovaMixedConfig
from pystatkit.core.data_loader import filter_dv
from pystatkit.core.results import AnalysisResult


def _descriptives_cell(
    df: pd.DataFrame, dv: str, between: str, within: str
) -> pd.DataFrame:
    """Mean, SD, n for each (between × within) cell."""
    return df.groupby([between, within], observed=True)[dv].agg(
        n="count", mean="mean", sd="std", median="median"
    )


def _format_mixed_interpretation(primary: pd.DataFrame, outcome: str) -> str:
    """APA-style sentence per effect row."""
    sentences = []
    for _, row in primary.iterrows():
        source = row["Source"]
        f = row["F"]
        df1 = int(row["DF1"])
        df2 = int(row["DF2"])
        p = row["p_unc"]
        np2 = row.get("np2", float("nan"))

        if pd.isna(f):
            continue

        p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
        np2_str = f"{np2:.3f}" if pd.notna(np2) else "n/a"

        sentences.append(
            f"{source}: F({df1}, {df2}) = {f:.2f}, p {p_str}, "
            f"partial eta-squared = {np2_str}."
        )
    return f"Mixed ANOVA effects on {outcome}. " + " ".join(sentences)


def _simple_effects(
    df: pd.DataFrame, cfg: AnovaMixedConfig, subject: str
) -> pd.DataFrame:
    """Follow up a significant interaction: within effect at each between level."""
    rows = []
    for level, sub in df.groupby(cfg.between, observed=True):
        if sub[subject].nunique() < 2:
            continue
        try:
            res = pg.rm_anova(
                data=sub,
                dv=cfg.outcome,
                within=cfg.within,
                subject=subject,
                detailed=False,
            )
            eff = res.iloc[0]
            rows.append(
                {
                    f"{cfg.between}_level": level,
                    "effect": f"{cfg.within} (simple)",
                    "F": eff.get("F"),
                    "DF": eff.get("DF") if "DF" in eff else eff.get("ddof1"),
                    "p_unc": eff.get("p_unc"),
                    "np2": eff.get("np2", eff.get("ng2")),
                    "n_subjects": sub[subject].nunique(),
                }
            )
        except Exception as e:
            rows.append(
                {f"{cfg.between}_level": level, "error": str(e)[:80]}
            )
    return pd.DataFrame(rows)


def mixed_anova(
    df: pd.DataFrame, cfg: AnovaMixedConfig, id_col: str
) -> AnalysisResult:
    """Mixed ANOVA: one within × one between factor."""
    df = filter_dv(df, cfg.outcome)
    subject = cfg.id or id_col

    primary = pg.mixed_anova(
        data=df,
        dv=cfg.outcome,
        within=cfg.within,
        between=cfg.between,
        subject=subject,
        correction=cfg.sphericity_correction != "none",
    )

    # Post-hoc pairwise comparisons (interaction-aware).
    posthoc = None
    if cfg.posthoc != "none":
        padjust = cfg.posthoc if cfg.posthoc in ("holm", "bonferroni", "fdr_bh") else "holm"
        try:
            posthoc = pg.pairwise_tests(
                data=df,
                dv=cfg.outcome,
                within=cfg.within,
                between=cfg.between,
                subject=subject,
                padjust=padjust,
                interaction=True,
            )
        except Exception as e:
            # Some combinations of factors raise; keep primary + note.
            print(f"[pystatkit] Note: mixed post-hoc failed ({e}); continuing.")

    # Simple effects when interaction row is significant.
    simple = None
    interaction_row = primary[primary["Source"] == "Interaction"]
    interaction_sig = (
        cfg.simple_effects
        and not interaction_row.empty
        and float(interaction_row["p_unc"].iloc[0]) < 0.05
    )
    if interaction_sig:
        simple = _simple_effects(df, cfg, subject)

    # Effect sizes.
    es: dict[str, float] = {}
    for _, row in primary.iterrows():
        if pd.notna(row.get("np2")):
            es[f"{row['Source']}_partial_eta_sq"] = float(row["np2"])

    interpretation = _format_mixed_interpretation(primary, cfg.outcome)
    if interaction_sig and simple is not None and not simple.empty:
        interpretation += " Interaction was significant; simple effects of within factor examined at each between-group level (see extras)."

    descriptives = _descriptives_cell(df, cfg.outcome, cfg.between, cfg.within)

    return AnalysisResult(
        method="Mixed ANOVA",
        method_key="anova_mixed",
        primary=primary,
        posthoc=posthoc,
        descriptives=descriptives,
        effect_size=es,
        n_total=int(df[subject].nunique()),
        interpretation=interpretation,
        extras={
            "within": cfg.within,
            "between": cfg.between,
            "simple_effects": simple,
            "posthoc_method": cfg.posthoc,
        },
    )
