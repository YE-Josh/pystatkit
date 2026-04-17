"""pystatkit CLI (v0.2).

Loads a StudyConfig, loads the data once, then runs every enabled method
via the orchestrator. Outputs for all methods are written under a single
``output.dir`` using ``<basename>_<method>.{docx,xlsx}``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pystatkit.core.config import load_config
from pystatkit.core.data_loader import hash_data, load_data
from pystatkit.core.orchestrator import MethodRun, run_study
from pystatkit.core.provenance import get_run_metadata
from pystatkit.io.apa_formatter import write_docx_report, write_xlsx_report

logger = logging.getLogger("pystatkit")


def _setup_logging(log_dir: Path, basename: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{basename}.log"
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def _interactive_confirm(method_label: str) -> bool:
    prompt = (
        f"\nProceed with '{method_label}'? "
        f"[Y]es / [n]o (skip this method): "
    )
    response = input(prompt).strip().lower()
    return response in ("", "y", "yes")


def _write_outputs(
    runs: list[MethodRun],
    config,
    metadata,
) -> None:
    """Write docx/xlsx for every successful method run."""
    config.output.dir.mkdir(parents=True, exist_ok=True)
    base = config.output.basename

    for run in runs:
        if run.skipped or run.result is None:
            continue

        stem = config.output.dir / f"{base}_{run.method_key}"

        if "docx" in config.output.formats:
            write_docx_report(run.result, metadata, stem.with_suffix(".docx"))
            logger.info(f"Wrote: {stem.with_suffix('.docx')}")

        if "xlsx" in config.output.formats:
            write_xlsx_report(run.result, metadata, stem.with_suffix(".xlsx"))
            logger.info(f"Wrote: {stem.with_suffix('.xlsx')}")


def _print_summary(runs: list[MethodRun]) -> None:
    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    for run in runs:
        status = "SKIPPED" if run.skipped else "OK"
        print(f"  [{status}] {run.method_key}: {run.method_name}")
        if run.skipped:
            print(f"           reason: {run.skip_reason}")
        elif run.result is not None:
            print(f"           {run.result.interpretation}")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pystatkit",
        description="Run all enabled methods from a YAML config.",
    )
    parser.add_argument("--config", "-c", required=True, type=Path)
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the interactive confirmation after each assumption check.",
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)

    _setup_logging(config.output.dir / "logs", config.output.basename)
    logger.info("pystatkit v0.2 run started")
    logger.info(f"Config:  {args.config}")
    logger.info(f"Study:   {config.study.name}")
    logger.info(
        f"Enabled: {[m.name for m in config.enabled_methods()]}"
    )

    df = load_data(config)
    data_hash = hash_data(df)
    logger.info(f"Data loaded: {len(df)} rows, hash={data_hash}")

    confirm_cb = None
    if config.defaults.confirm_method and not args.no_confirm:
        confirm_cb = _interactive_confirm

    runs = run_study(df, config, confirm_callback=confirm_cb)

    metadata = get_run_metadata(data_hash=data_hash, config_path=args.config)
    _write_outputs(runs, config, metadata)

    _print_summary(runs)

    # Non-zero exit if any method was skipped due to an error (not user choice).
    errored = [r for r in runs if r.skipped and "declined" not in r.skip_reason]
    return 1 if errored else 0


if __name__ == "__main__":
    sys.exit(main())
