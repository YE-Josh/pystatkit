"""Core infrastructure: config loading, data validation, assumption checks, results."""

from pystatkit.core.config import AnalysisConfig, load_config
from pystatkit.core.data_loader import load_data, validate_schema
from pystatkit.core.assumptions import run_assumption_checks, AssumptionReport
from pystatkit.core.results import AnalysisResult
from pystatkit.core.provenance import get_run_metadata

__all__ = [
    "AnalysisConfig",
    "load_config",
    "load_data",
    "validate_schema",
    "run_assumption_checks",
    "AssumptionReport",
    "AnalysisResult",
    "get_run_metadata",
]
