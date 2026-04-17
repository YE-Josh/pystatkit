"""Demographic / Table 1 generation via tableone.

Table 1 auto-selects comparison tests per-variable-type (t-test for
normal continuous, ANOVA for multi-group continuous, chi-squared for
categorical, etc.). This is standard descriptive practice — not a
violation of human-in-the-loop — because Table 1 is always presented
as descriptive context rather than as the inferential result of interest.
"""

from __future__ import annotations

import pandas as pd
from tableone import TableOne

from pystatkit.core.config import DemographicConfig
from pystatkit.core.results import AnalysisResult


def demographic(df: pd.DataFrame, cfg: DemographicConfig) -> AnalysisResult:
    """Build Table 1 from the dataset.

    For multi-row-per-subject datasets (e.g. long-format with repeated
    measures), `group_by` should be a per-subject attribute; tableone will
    treat each row as an observation. If your dataset has repeated rows per
    subject, collapse to one-row-per-subject before running demographic.
    """
    # Restrict to the columns of interest + group_by if any.
    cols: list[str] = [*cfg.continuous, *cfg.categorical]
    if cfg.group_by:
        cols = cols + [cfg.group_by]
    sub = df[cols].copy()

    # Many studies store demographics once per subject but the long-format
    # data repeats them across rows. Dedupe on all selected columns to avoid
    # double-counting subjects with multiple trials.
    before = len(sub)
    sub = sub.drop_duplicates()
    if len(sub) < before:
        print(
            f"[pystatkit] demographic: deduplicated {before - len(sub)} repeated "
            f"row(s). Using {len(sub)} unique subject records."
        )

    # tableone auto-handles mean_sd vs median_iqr via `nonnormal`.
    nonnormal = list(cfg.nonnormal)
    if cfg.continuous_summary == "median_iqr":
        # Force all continuous vars to median [IQR].
        nonnormal = list(cfg.continuous)

    t1 = TableOne(
        sub,
        columns=[*cfg.continuous, *cfg.categorical],
        categorical=list(cfg.categorical),
        groupby=cfg.group_by,
        nonnormal=nonnormal,
        pval=cfg.include_tests and bool(cfg.group_by),
        overall=cfg.overall_column,
    )

    # Flatten the MultiIndex columns for easy downstream formatting.
    table_df = t1.tableone.copy()
    if isinstance(table_df.columns, pd.MultiIndex):
        table_df.columns = [
            col[1] if isinstance(col, tuple) else col for col in table_df.columns
        ]
    table_df = table_df.reset_index()

    # A one-line summary sentence for the APA text block.
    group_phrase = f" by {cfg.group_by}" if cfg.group_by else ""
    n_total = len(sub)
    n_cont = len(cfg.continuous)
    n_cat = len(cfg.categorical)
    interpretation = (
        f"Demographic table for {n_total} participants{group_phrase}: "
        f"{n_cont} continuous variable(s), {n_cat} categorical variable(s)."
    )

    return AnalysisResult(
        method="Demographic table",
        method_key="demographic",
        primary=table_df,
        descriptives=None,  # the table itself IS the descriptives
        effect_size={},
        n_total=n_total,
        interpretation=interpretation,
        extras={
            "group_by": cfg.group_by,
            "continuous": list(cfg.continuous),
            "categorical": list(cfg.categorical),
            "nonnormal": nonnormal,
        },
    )
