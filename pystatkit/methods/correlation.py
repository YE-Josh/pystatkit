"""Pairwise correlations: Pearson, Spearman, Kendall."""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import CorrelationConfig
from pystatkit.core.results import AnalysisResult


def correlation(df: pd.DataFrame, cfg: CorrelationConfig) -> AnalysisResult:
    """Compute pairwise correlations among `cfg.vars`.

    Returns a long-format table (one row per variable pair) with r, n, CI,
    p-value, and power. A wide correlation matrix is also attached to
    `extras` when `cfg.matrix_output` is True.

    If the selected variables are identical across multiple rows (typical
    when long-format repeated-measures data has per-subject demographic
    columns duplicated across trials), duplicate rows are removed with a
    warning. Correlations assume independent observations, and analysing
    repeated rows would inflate the effective sample size.
    """
    sub = df[cfg.vars].copy()

    # Drop exact duplicate rows across the selected variables only.
    before = len(sub)
    sub = sub.drop_duplicates()
    if len(sub) < before:
        print(
            f"[pystatkit] correlation: detected {before - len(sub)} duplicate "
            f"row(s) across the selected variables; deduplicated to avoid "
            f"inflated n. Using {len(sub)} unique row(s)."
        )

    # Listwise deletion on the selected variables.
    sub_valid = sub.dropna()

    # Pairwise table.
    pairs = pg.pairwise_corr(sub_valid, columns=cfg.vars, method=cfg.method)

    # Correlation matrix (wide).
    matrix = sub_valid.corr(method=cfg.method) if cfg.matrix_output else None

    # Build a concise interpretation: count significant pairs.
    n_pairs = len(pairs)
    sig = int((pairs["p_unc"] < 0.05).sum())

    method_label = cfg.method.capitalize()
    interpretation = (
        f"{method_label} correlations among {len(cfg.vars)} variables: "
        f"{sig} of {n_pairs} pairwise correlation(s) significant at α = .05 "
        f"(n = {len(sub_valid)} with complete data)."
    )

    return AnalysisResult(
        method=f"{method_label} correlation",
        method_key="correlation",
        primary=pairs,
        descriptives=None,
        effect_size={},
        n_total=len(sub_valid),
        interpretation=interpretation,
        extras={
            "method": cfg.method,
            "variables": list(cfg.vars),
            "matrix": matrix,  # stored for formatter to render as second table
        },
    )
