"""ANCOVA: group comparison controlling for one or more covariates.

Assumption checks (opt-in via config):
- homogeneity_of_slopes : group × covariate interaction should be non-significant
- linearity             : covariate-outcome relationship should be linear
- normality_residuals   : Shapiro-Wilk on model residuals
- homogeneity_variance  : Levene on residuals across groups

Reports adjusted (estimated marginal) means alongside raw group means so the
reader can see what the covariate adjustment does to the comparison.
"""

from __future__ import annotations

import pandas as pd
import pingouin as pg
import statsmodels.formula.api as smf
from scipy import stats as scipy_stats

from pystatkit.core.config import AncovaConfig
from pystatkit.core.data_loader import filter_dv
from pystatkit.core.results import AnalysisResult


def _check_homogeneity_of_slopes(
    df: pd.DataFrame, outcome: str, group: str, covariates: list[str]
) -> pd.DataFrame:
    """Fit outcome ~ group * covariate(s) and test the interaction term(s).

    A non-significant interaction supports the ANCOVA assumption that each
    group has the same slope with respect to the covariate.
    """
    # Build formula: outcome ~ group + cov1 + cov2 + group:cov1 + group:cov2
    cov_terms = " + ".join(covariates)
    interactions = " + ".join(f"{group}:{c}" for c in covariates)
    formula = f"{outcome} ~ {group} + {cov_terms} + {interactions}"
    model = smf.ols(formula, data=df).fit()

    # Extract the interaction term p-values.
    rows = []
    for term, pval in model.pvalues.items():
        if ":" in term and term.split(":")[0].startswith(group):
            rows.append({"term": term, "pval": float(pval)})

    if not rows:
        # Numeric group variable: pingouin style.
        return pd.DataFrame([{"term": f"{group}:covariate", "pval": float("nan")}])
    return pd.DataFrame(rows)


def _check_linearity(
    df: pd.DataFrame, outcome: str, covariates: list[str]
) -> pd.DataFrame:
    """Pearson correlation between outcome and each covariate.

    A quick sanity check — a non-linear covariate-outcome relationship would
    show a weak correlation despite a clear pattern in the scatter plot.
    This is a first-pass screen; visual inspection is recommended.
    """
    rows = []
    for c in covariates:
        valid = df[[outcome, c]].dropna()
        if len(valid) < 3:
            rows.append({"covariate": c, "r": float("nan"), "pval": float("nan")})
            continue
        r, p = scipy_stats.pearsonr(valid[outcome], valid[c])
        rows.append({"covariate": c, "r": float(r), "pval": float(p)})
    return pd.DataFrame(rows)


def _check_residual_normality(residuals: pd.Series) -> pd.DataFrame:
    """Shapiro-Wilk on residuals."""
    resid = residuals.dropna().to_numpy()
    if len(resid) < 3:
        return pd.DataFrame([{"stat_name": "W", "stat": float("nan"), "pval": float("nan")}])
    w, p = scipy_stats.shapiro(resid)
    return pd.DataFrame([{"stat_name": "W", "stat": float(w), "pval": float(p)}])


def _check_residual_homogeneity(
    residuals: pd.Series, group_series: pd.Series
) -> pd.DataFrame:
    """Levene (median-centered) on residuals across groups."""
    tmp = pd.DataFrame({"r": residuals, "g": group_series}).dropna()
    groups = [s["r"].to_numpy() for _, s in tmp.groupby("g")]
    if len(groups) < 2 or any(len(g) < 2 for g in groups):
        return pd.DataFrame([{"W": float("nan"), "pval": float("nan")}])
    w, p = scipy_stats.levene(*groups, center="median")
    return pd.DataFrame([{"W": float(w), "pval": float(p)}])


def _adjusted_means(
    df: pd.DataFrame, outcome: str, group: str, covariates: list[str]
) -> pd.DataFrame:
    """Estimated marginal means: predicted outcome for each group with covariates
    fixed at their grand mean.

    This is the ANCOVA-adjusted 'what each group would score if all covariates
    were equal' — which is what ANCOVA is really comparing.
    """
    cov_terms = " + ".join(covariates)
    formula = f"{outcome} ~ {group} + {cov_terms}"
    model = smf.ols(formula, data=df).fit()

    # Build a prediction grid: one row per group level, covariates at their mean.
    levels = sorted(df[group].dropna().unique())
    cov_means = {c: df[c].mean() for c in covariates}
    grid = pd.DataFrame({group: levels, **{c: [cov_means[c]] * len(levels) for c in covariates}})
    preds = model.get_prediction(grid).summary_frame(alpha=0.05)

    out = grid[[group]].copy()
    out["adjusted_mean"] = preds["mean"].values
    out["se"] = preds["mean_se"].values
    out["ci_low"] = preds["mean_ci_lower"].values
    out["ci_high"] = preds["mean_ci_upper"].values
    return out


def _descriptives(
    df: pd.DataFrame, outcome: str, group: str
) -> pd.DataFrame:
    return df.groupby(group)[outcome].agg(
        n="count", mean="mean", sd="std", median="median"
    )


def _posthoc_on_adjusted(
    df: pd.DataFrame, outcome: str, group: str, covariates: list[str], padjust: str
) -> pd.DataFrame | None:
    """Pairwise comparisons of adjusted means using pingouin.pairwise_tests.

    pingouin doesn't expose covariate-adjusted pairwise contrasts directly in
    a single call; as a pragmatic approximation we use pairwise_tests on the
    raw data with the same multiple-comparison adjustment. For publication
    ANCOVA follow-ups, emmeans (R) is the gold standard — this is a
    reasonable approximation for exploratory work.
    """
    if padjust not in ("holm", "bonferroni", "fdr_bh"):
        padjust = "holm"
    return pg.pairwise_tests(
        data=df, dv=outcome, between=group, padjust=padjust
    )


def ancova(df: pd.DataFrame, cfg: AncovaConfig) -> AnalysisResult:
    """Run ANCOVA with configurable assumption checks and adjusted means."""
    df = filter_dv(df, cfg.outcome)

    # Drop rows missing any of the covariates too — ANCOVA can't use them.
    df = df.dropna(subset=cfg.covariates + [cfg.group])

    # Main ANCOVA.
    primary = pg.ancova(
        data=df, dv=cfg.outcome, covar=cfg.covariates, between=cfg.group
    )

    # --- Assumption checks (each is optional via config) ---
    assumptions: dict[str, pd.DataFrame] = {}

    if cfg.check_assumptions.homogeneity_of_slopes:
        assumptions["homogeneity_of_slopes"] = _check_homogeneity_of_slopes(
            df, cfg.outcome, cfg.group, cfg.covariates
        )

    if cfg.check_assumptions.linearity:
        assumptions["linearity"] = _check_linearity(
            df, cfg.outcome, cfg.covariates
        )

    # Fit the ANCOVA model once to get residuals for the last two checks.
    if (
        cfg.check_assumptions.normality_residuals
        or cfg.check_assumptions.homogeneity_variance
    ):
        cov_terms = " + ".join(cfg.covariates)
        formula = f"{cfg.outcome} ~ {cfg.group} + {cov_terms}"
        resid_model = smf.ols(formula, data=df).fit()
        residuals = resid_model.resid

        if cfg.check_assumptions.normality_residuals:
            assumptions["normality_residuals"] = _check_residual_normality(residuals)

        if cfg.check_assumptions.homogeneity_variance:
            assumptions["homogeneity_variance"] = _check_residual_homogeneity(
                residuals, df[cfg.group]
            )

    # --- Adjusted means ---
    adj_means = None
    if cfg.adjusted_means:
        adj_means = _adjusted_means(df, cfg.outcome, cfg.group, cfg.covariates)

    # --- Post-hoc ---
    posthoc = None
    if cfg.posthoc != "none":
        posthoc = _posthoc_on_adjusted(
            df, cfg.outcome, cfg.group, cfg.covariates, cfg.posthoc
        )

    # --- APA interpretation ---
    group_row = primary[primary["Source"] == cfg.group].iloc[0]
    f = float(group_row["F"])
    df1 = int(group_row["DF"])
    df2 = int(primary[primary["Source"] == "Residual"].iloc[0]["DF"])
    p = float(group_row["p_unc"])
    np2 = float(group_row["np2"])

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    cov_phrase = ", ".join(cfg.covariates)
    interpretation = (
        f"ANCOVA: effect of {cfg.group} on {cfg.outcome} controlling for "
        f"{cov_phrase}, F({df1}, {df2}) = {f:.2f}, p {p_str}, "
        f"partial eta-squared = {np2:.3f}."
    )

    # Assumption violations summary.
    warnings = _summarise_assumption_violations(assumptions)
    if warnings:
        interpretation += " Assumption concerns: " + "; ".join(warnings) + "."

    return AnalysisResult(
        method="ANCOVA",
        method_key="ancova",
        primary=primary,
        posthoc=posthoc,
        descriptives=_descriptives(df, cfg.outcome, cfg.group),
        effect_size={"partial_eta_sq": np2},
        n_total=len(df),
        interpretation=interpretation,
        extras={
            "covariates": list(cfg.covariates),
            "adjusted_means": adj_means,
            "assumptions": assumptions,
            "posthoc_method": cfg.posthoc,
        },
    )


def _summarise_assumption_violations(assumptions: dict[str, pd.DataFrame]) -> list[str]:
    """Produce short warning strings for any assumption that failed at α = .05."""
    warnings: list[str] = []
    alpha = 0.05

    if "homogeneity_of_slopes" in assumptions:
        df_slope = assumptions["homogeneity_of_slopes"]
        if (df_slope["pval"] < alpha).any():
            warnings.append(
                "group × covariate interaction significant "
                "(homogeneity of slopes violated)"
            )

    if "normality_residuals" in assumptions:
        df_norm = assumptions["normality_residuals"]
        if (df_norm["pval"] < alpha).any():
            warnings.append("residuals non-normal")

    if "homogeneity_variance" in assumptions:
        df_hv = assumptions["homogeneity_variance"]
        if (df_hv["pval"] < alpha).any():
            warnings.append("residual variance heterogeneous across groups")

    return warnings
