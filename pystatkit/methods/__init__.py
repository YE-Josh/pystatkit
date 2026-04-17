"""Statistical method implementations.

Each method is a small function that takes a DataFrame and config,
and returns a populated AnalysisResult. A dispatcher selects the right
one based on `config.method`.

All computations rely on pingouin/scipy — this module is an orchestration
and standardization layer, not a re-implementation of statistical tests.
"""

from __future__ import annotations

import pandas as pd

from pystatkit.core.config import AnalysisConfig
from pystatkit.core.results import AnalysisResult
from pystatkit.methods import one_way_anova, paired, two_group


# Method dispatch table. Maps config.method -> callable.
# Keeping this explicit (rather than dynamic) makes it easy to see what
# methods exist and to add new ones later.
_DISPATCH = {
    # two-group independent
    "independent_t": two_group.independent_t,
    "welch_t": two_group.welch_t,
    "mann_whitney": two_group.mann_whitney,
    # two-group paired
    "paired_t": paired.paired_t,
    "wilcoxon": paired.wilcoxon,
    # one-way ANOVA family
    "anova": one_way_anova.one_way_anova,
    "kruskal_wallis": one_way_anova.kruskal_wallis,
}


def run_analysis(df: pd.DataFrame, config: AnalysisConfig) -> AnalysisResult:
    """Dispatch to the correct method based on `config.method`.

    Parameters
    ----------
    df : pd.DataFrame
        Input data in long format.
    config : AnalysisConfig
        Validated configuration.

    Returns
    -------
    AnalysisResult
        The analysis output, standardized across methods.
    """
    if config.method not in _DISPATCH:
        raise ValueError(
            f"Method '{config.method}' is not implemented. "
            f"Available methods: {list(_DISPATCH.keys())}"
        )
    return _DISPATCH[config.method](df, config)


__all__ = ["run_analysis"]
