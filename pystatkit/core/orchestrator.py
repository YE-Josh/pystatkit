"""Orchestrator: runs all enabled methods in a StudyConfig.

The orchestrator is the glue between config, data, assumption checks, method
dispatch, and output. It does not implement statistics itself — it coordinates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pystatkit.core.assumptions import AssumptionReport, run_assumption_checks
from pystatkit.core.config import (
    AnovaOnewayConfig,
    MethodConfig,
    PairedConfig,
    StudyConfig,
    TwoGroupConfig,
)
from pystatkit.core.data_loader import validate_data_columns
from pystatkit.core.results import AnalysisResult
from pystatkit.methods import run_method

logger = logging.getLogger("pystatkit")


@dataclass
class MethodRun:
    """Bundles everything produced by running one method."""

    method_key: str
    method_name: str
    assumptions: AssumptionReport | None
    result: AnalysisResult | None
    skipped: bool = False
    skip_reason: str = ""


# Methods that have assumption checks implemented as of v0.2.1 of orchestrator.
_ASSUMPTION_CAPABLE = (TwoGroupConfig, PairedConfig, AnovaOnewayConfig)


def run_study(
    df: pd.DataFrame, config: StudyConfig, confirm_callback=None
) -> list[MethodRun]:
    """Run all enabled methods in the config, returning one MethodRun each.

    Parameters
    ----------
    df : pd.DataFrame
        The already-loaded dataset.
    config : StudyConfig
        Validated study configuration.
    confirm_callback : callable or None
        Optional ``(method_name: str) -> bool`` function. Called after
        assumption checks for each method; if it returns False, that
        method is skipped. When None, no confirmation is requested.

    Returns
    -------
    list[MethodRun]
        One entry per enabled method, in config order.
    """
    runs: list[MethodRun] = []

    for method_cfg in config.enabled_methods():
        logger.info(f"--- Running method: {method_cfg.name} ---")

        # Per-method column validation.
        try:
            validate_data_columns(df, method_cfg, config.data)
        except ValueError as e:
            logger.error(f"Column validation failed for {method_cfg.name}: {e}")
            runs.append(
                MethodRun(
                    method_key=method_cfg.name,
                    method_name=method_cfg.name,
                    assumptions=None,
                    result=None,
                    skipped=True,
                    skip_reason=str(e),
                )
            )
            continue

        # Assumption checks where implemented.
        assumptions: AssumptionReport | None = None
        if isinstance(method_cfg, _ASSUMPTION_CAPABLE):
            assumptions = run_assumption_checks(
                df, method_cfg, id_col=config.data.id_col
            )
            print()
            print(f"[{method_cfg.name}]")
            print(assumptions.to_text(alpha=config.defaults.alpha))

        # Human-in-the-loop confirmation.
        if confirm_callback is not None:
            # Display method being run to user for confirmation.
            method_display = _method_display_name(method_cfg)
            if not confirm_callback(method_display):
                logger.info(f"Method {method_cfg.name} skipped by user.")
                runs.append(
                    MethodRun(
                        method_key=method_cfg.name,
                        method_name=method_display,
                        assumptions=assumptions,
                        result=None,
                        skipped=True,
                        skip_reason="User declined after assumption review.",
                    )
                )
                continue

        # Dispatch — some methods (demographic, correlation, ANCOVA, RM/mixed
        # ANOVA) are not yet wired into run_method; those land here as
        # NotImplementedError and are reported as skipped until later stages
        # of v0.2 land them.
        try:
            result = run_method(df, method_cfg, id_col=config.data.id_col)
            runs.append(
                MethodRun(
                    method_key=method_cfg.name,
                    method_name=result.method,
                    assumptions=assumptions,
                    result=result,
                )
            )
            logger.info(
                f"{method_cfg.name} complete: n={result.n_total}, "
                f"method={result.method}"
            )
        except NotImplementedError as e:
            logger.warning(f"{method_cfg.name} not yet implemented: {e}")
            runs.append(
                MethodRun(
                    method_key=method_cfg.name,
                    method_name=method_cfg.name,
                    assumptions=assumptions,
                    result=None,
                    skipped=True,
                    skip_reason=f"Not implemented yet: {e}",
                )
            )

    return runs


def _method_display_name(cfg: MethodConfig) -> str:
    """Produce a human-friendly method label for confirmation prompts."""
    if isinstance(cfg, (TwoGroupConfig, PairedConfig, AnovaOnewayConfig)):
        return f"{cfg.name} → {cfg.method}"
    return cfg.name
