"""Data loading and per-method column validation.

In v0.2 the data is loaded ONCE for the whole run, then each method validates
the columns it needs against the already-loaded DataFrame. This avoids
re-reading the file for each method and lets us cache the data hash.
"""

from __future__ import annotations

import hashlib

import pandas as pd

from pystatkit.core.config import DataConfig, MethodConfig, StudyConfig


def load_data(config: StudyConfig) -> pd.DataFrame:
    """Load the dataset specified in `config.data`."""
    path = config.data.file
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=config.data.sheet or 0)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .csv or .xlsx.")

    return df


def _required_columns(method_cfg: MethodConfig, data_cfg: DataConfig) -> list[str]:
    """Return the set of columns a given method needs in the DataFrame.

    Centralizes schema expectations so validation is consistent.
    """
    from pystatkit.core.config import (
        AncovaConfig,
        AnovaMixedConfig,
        AnovaOnewayConfig,
        AnovaRMConfig,
        CorrelationConfig,
        DemographicConfig,
        PairedConfig,
        TwoGroupConfig,
    )

    cols: list[str] = []

    if isinstance(method_cfg, DemographicConfig):
        cols.extend(method_cfg.continuous)
        cols.extend(method_cfg.categorical)
        if method_cfg.group_by:
            cols.append(method_cfg.group_by)

    elif isinstance(method_cfg, TwoGroupConfig):
        cols.extend([method_cfg.outcome, method_cfg.group])

    elif isinstance(method_cfg, PairedConfig):
        id_col = method_cfg.id or data_cfg.id_col
        cols.extend([method_cfg.outcome, method_cfg.condition, id_col])

    elif isinstance(method_cfg, AnovaOnewayConfig):
        cols.extend([method_cfg.outcome, method_cfg.group])

    elif isinstance(method_cfg, AnovaRMConfig):
        id_col = method_cfg.id or data_cfg.id_col
        cols.append(method_cfg.outcome)
        cols.extend(method_cfg.within)
        cols.append(id_col)

    elif isinstance(method_cfg, AnovaMixedConfig):
        id_col = method_cfg.id or data_cfg.id_col
        cols.extend(
            [method_cfg.outcome, method_cfg.within, method_cfg.between, id_col]
        )

    elif isinstance(method_cfg, CorrelationConfig):
        cols.extend(method_cfg.vars)

    elif isinstance(method_cfg, AncovaConfig):
        cols.extend([method_cfg.outcome, method_cfg.group])
        cols.extend(method_cfg.covariates)

    return [c for c in cols if c]  # drop Nones


def validate_data_columns(
    df: pd.DataFrame, method_cfg: MethodConfig, data_cfg: DataConfig
) -> None:
    """Verify that `df` contains all columns required by `method_cfg`."""
    required = _required_columns(method_cfg, data_cfg)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Method '{method_cfg.name}' requires columns {missing}, "
            f"but they are not in the data. Available columns: {list(df.columns)}"
        )


def hash_data(df: pd.DataFrame) -> str:
    """Short SHA-256 hash of the DataFrame content (for provenance)."""
    hasher = hashlib.sha256()
    hasher.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return hasher.hexdigest()[:12]


def filter_dv(df: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Return rows with a non-null outcome — used before tests on a specific DV."""
    return df[df[outcome].notna()].copy()
