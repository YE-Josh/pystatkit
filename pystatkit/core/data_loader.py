"""Data loading and long-format schema validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from pystatkit.core.config import AnalysisConfig


def load_data(config: AnalysisConfig) -> pd.DataFrame:
    """Load a dataset from .csv or .xlsx according to the config.

    Parameters
    ----------
    config : AnalysisConfig
        Configuration specifying the data file and (optionally) sheet.

    Returns
    -------
    pd.DataFrame
        The loaded data.
    """
    path = config.data_file
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=config.sheet or 0)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .csv or .xlsx.")

    return df


def validate_schema(df: pd.DataFrame, config: AnalysisConfig) -> None:
    """Verify that the DataFrame contains the required columns for the analysis.

    Raises
    ------
    ValueError
        If a required column is missing or contains unexpected data.
    """
    required: list[str] = [config.dv]
    if config.group:
        required.append(config.group)
    if config.subject:
        required.append(config.subject)
    if config.condition:
        required.append(config.condition)

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in data: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # DV must be numeric.
    if not pd.api.types.is_numeric_dtype(df[config.dv]):
        raise ValueError(
            f"Dependent variable '{config.dv}' must be numeric, "
            f"got dtype {df[config.dv].dtype}."
        )

    # Warn on missing values in DV.
    n_missing = df[config.dv].isna().sum()
    if n_missing > 0:
        print(
            f"[pystatkit] Warning: {n_missing} missing value(s) in '{config.dv}'. "
            f"These will be dropped by the statistical routine."
        )

    # Group-specific checks — only count groups with actual DV data.
    df_valid = df[df[config.dv].notna()]

    if config.design == "two_group_independent":
        n_groups = df_valid[config.group].nunique()
        if n_groups != 2:
            raise ValueError(
                f"Two-group design requires exactly 2 levels in '{config.group}' "
                f"with valid DV data, found {n_groups}: "
                f"{sorted(df_valid[config.group].dropna().unique())}"
            )

    if config.design == "one_way_anova":
        n_groups = df_valid[config.group].nunique()
        if n_groups < 3:
            raise ValueError(
                f"One-way ANOVA requires at least 3 levels in '{config.group}', "
                f"found {n_groups}. Consider a two-group comparison instead."
            )

    if config.design == "two_group_paired":
        n_conditions = df_valid[config.condition].nunique()
        if n_conditions != 2:
            raise ValueError(
                f"Paired design requires exactly 2 levels in '{config.condition}', "
                f"found {n_conditions}."
            )


def hash_data(df: pd.DataFrame) -> str:
    """Compute a short SHA-256 hash of the DataFrame for provenance tracking.

    The hash is deterministic for the same data content and used in output
    metadata to allow tracing a result back to its exact input.
    """
    hasher = hashlib.sha256()
    # Use pandas' own bytes representation for determinism.
    hasher.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return hasher.hexdigest()[:12]
