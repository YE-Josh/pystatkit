"""Statistical method implementations.

Each method is a function taking (df, method_cfg, id_col) and returning an
AnalysisResult. A dispatcher routes to the correct method based on the
method config class + its `method` attribute.
"""

from __future__ import annotations

import pandas as pd

from pystatkit.core.config import (
    AncovaConfig,
    AnovaMixedConfig,
    AnovaOnewayConfig,
    AnovaRMConfig,
    CorrelationConfig,
    DemographicConfig,
    MethodConfig,
    PairedConfig,
    TwoGroupConfig,
)
from pystatkit.core.results import AnalysisResult
from pystatkit.methods import ancova as _ancova
from pystatkit.methods import anova_mixed as _anova_mixed
from pystatkit.methods import anova_rm as _anova_rm
from pystatkit.methods import correlation as _correlation
from pystatkit.methods import demographic as _demographic
from pystatkit.methods import one_way_anova, paired, two_group


def run_method(
    df: pd.DataFrame, method_cfg: MethodConfig, id_col: str
) -> AnalysisResult:
    """Dispatch to the concrete statistical method implementation."""
    if isinstance(method_cfg, DemographicConfig):
        return _demographic.demographic(df, method_cfg)

    if isinstance(method_cfg, TwoGroupConfig):
        return {
            "independent_t": two_group.independent_t,
            "welch_t": two_group.welch_t,
            "mann_whitney": two_group.mann_whitney,
        }[method_cfg.method](df, method_cfg)

    if isinstance(method_cfg, PairedConfig):
        return {
            "paired_t": paired.paired_t,
            "wilcoxon": paired.wilcoxon,
        }[method_cfg.method](df, method_cfg, id_col)

    if isinstance(method_cfg, AnovaOnewayConfig):
        return {
            "anova": one_way_anova.one_way_anova,
            "welch_anova": one_way_anova.welch_anova,
            "kruskal_wallis": one_way_anova.kruskal_wallis,
        }[method_cfg.method](df, method_cfg)

    if isinstance(method_cfg, AnovaRMConfig):
        return _anova_rm.rm_anova(df, method_cfg, id_col)

    if isinstance(method_cfg, AnovaMixedConfig):
        return _anova_mixed.mixed_anova(df, method_cfg, id_col)

    if isinstance(method_cfg, CorrelationConfig):
        return _correlation.correlation(df, method_cfg)

    if isinstance(method_cfg, AncovaConfig):
        return _ancova.ancova(df, method_cfg)

    raise NotImplementedError(
        f"No dispatcher registered for method config type {type(method_cfg).__name__}"
    )


__all__ = ["run_method"]
