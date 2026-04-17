"""Command-line interface for pystatkit.

Usage
-----
    pystatkit --config path/to/config.yaml
    pystatkit --config path/to/config.yaml --no-confirm   # skip interactive prompt

The CLI embodies the human-in-the-loop design: assumption checks are
reported and the user is asked to confirm the chosen method before the
analysis runs. Non-interactive runs (--no-confirm) are available for
scripting and reproducible pipelines.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pystatkit.core.assumptions import run_assumption_checks
from pystatkit.core.config import load_config
from pystatkit.core.data_loader import hash_data, load_data, validate_schema
from pystatkit.core.provenance import get_run_metadata
from pystatkit.io.apa_formatter import write_docx_report, write_xlsx_report
from pystatkit.methods import run_analysis

logger = logging.getLogger("pystatkit")


def _setup_logging(log_dir: Path, output_name: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{output_name}.log"

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def _confirm_method(method: str) -> bool:
    """Ask the user to confirm the chosen method after seeing assumption results."""
    print()
    prompt = (
        f"Proceed with method '{method}'? "
        f"[Y]es / [n]o (abort and edit config): "
    )
    response = input(prompt).strip().lower()
    return response in ("", "y", "yes")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, non-zero on error."""
    parser = argparse.ArgumentParser(
        prog="pystatkit",
        description=(
            "Run a single statistical analysis specified by a YAML config. "
            "Assumption checks are always reported; the chosen method is "
            "executed as specified."
        ),
    )
    parser.add_argument(
        "--config", "-c", required=True, type=Path, help="Path to config YAML."
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the interactive confirmation step (for scripted runs).",
    )
    args = parser.parse_args(argv)

    # Load config.
    config = load_config(args.config)

    # Set up logging into the output directory so logs are co-located with results.
    log_dir = config.output_dir.parent / "logs" if config.output_dir.name == "tables" \
        else config.output_dir / "logs"
    _setup_logging(log_dir, config.output_name)

    logger.info("pystatkit run started")
    logger.info(f"Config: {args.config}")
    logger.info(f"Design: {config.design}  Method: {config.method}")

    # Load and validate data.
    df = load_data(config)
    validate_schema(df, config)
    data_hash = hash_data(df)
    logger.info(f"Data loaded: {len(df)} rows, hash={data_hash}")

    # Filter to rows with a valid DV — multi-DV datasets often have NaN-padded rows.
    n_before = len(df)
    df = df[df[config.dv].notna()].copy()
    if len(df) < n_before:
        logger.info(
            f"Filtered to {len(df)} rows with non-null '{config.dv}' "
            f"(dropped {n_before - len(df)})."
        )

    # Run assumption checks and display.
    assumptions = run_assumption_checks(df, config)
    print()
    print(assumptions.to_text(alpha=config.alpha))

    # Human-in-the-loop confirmation.
    if config.confirm_method and not args.no_confirm:
        if not _confirm_method(config.method):
            logger.info("User aborted after reviewing assumption checks.")
            print("Aborted. Edit the config and re-run.")
            return 1

    # Run the analysis.
    result = run_analysis(df, config)
    logger.info(f"Analysis complete: {result.method}, n={result.n_total}")

    # Collect provenance.
    metadata = get_run_metadata(data_hash=data_hash, config_path=args.config)

    # Write outputs.
    config.output_dir.mkdir(parents=True, exist_ok=True)
    docx_path = config.output_dir / f"{config.output_name}.docx"
    xlsx_path = config.output_dir / f"{config.output_name}.xlsx"

    write_docx_report(result, metadata, docx_path)
    write_xlsx_report(result, metadata, xlsx_path)

    logger.info(f"Wrote: {docx_path}")
    logger.info(f"Wrote: {xlsx_path}")

    # Echo the APA interpretation to the console for quick copy/paste.
    print()
    print("=== Result ===")
    print(result.interpretation)
    print()
    print(f"Outputs: {docx_path}  and  {xlsx_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
