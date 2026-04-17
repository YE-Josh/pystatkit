"""Core infrastructure: config, data loading, assumption checks, results, provenance."""

from pystatkit.core.config import (
    AncovaAssumptions,
    AncovaConfig,
    AnovaMixedConfig,
    AnovaOnewayConfig,
    AnovaRMConfig,
    CorrelationConfig,
    DataConfig,
    Defaults,
    DemographicConfig,
    METHOD_REGISTRY,
    MethodConfig,
    OutputConfig,
    PairedConfig,
    StudyConfig,
    StudyMetadata,
    TwoGroupConfig,
    load_config,
)
from pystatkit.core.data_loader import hash_data, load_data, validate_data_columns
from pystatkit.core.results import AnalysisResult
from pystatkit.core.provenance import get_run_metadata

__all__ = [
    "AncovaAssumptions",
    "AncovaConfig",
    "AnovaMixedConfig",
    "AnovaOnewayConfig",
    "AnovaRMConfig",
    "CorrelationConfig",
    "DataConfig",
    "Defaults",
    "DemographicConfig",
    "METHOD_REGISTRY",
    "MethodConfig",
    "OutputConfig",
    "PairedConfig",
    "StudyConfig",
    "StudyMetadata",
    "TwoGroupConfig",
    "load_config",
    "hash_data",
    "load_data",
    "validate_data_columns",
    "AnalysisResult",
    "get_run_metadata",
]
