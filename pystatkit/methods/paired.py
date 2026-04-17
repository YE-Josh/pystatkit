"""Paired (within-subject) two-condition comparisons."""

from __future__ import annotations

import pandas as pd
import pingouin as pg

from pystatkit.core.config import PairedConfig
from pystatkit.core.data_loader import filter_dv
from pystatkit.core.results import AnalysisResult


def _to_wide(
    df: pd.DataFrame, dv: str, subject: str, condition: str
) -> pd.DataFrame:
    wide = df.pivot_table(index=subject, columns=condition, values=dv)
    if wide.shape[1] != 2:
        raise ValueError(
            f"Paired design requires exactly 2 conditions, "
            f"found {wide.shape[1]}: {list(wide.columns)}"
        )
    before = len(wide)
    wide = wide.dropna()
    if len(wide) < before:
        print(f"[pystatkit] Note: dropped {before - len(wide)} subject(s) with incomplete pairs.")
    return wide


def _descriptives_paired(wide: pd.DataFrame) -> pd.DataFrame:
    desc = wide.agg(["count", "mean", "std", "median"]).T
    desc.columns = ["n", "mean", "sd", "median"]
    diff = wide.iloc[:, 0] - wide.iloc[:, 1]
    desc.loc["difference"] = [len(diff), diff.mean(), diff.std(), diff.median()]
    return desc


def paired_t(
    df: pd.DataFrame, cfg: PairedConfig, id_col: str
) -> AnalysisResult:
    df = filter_dv(df, cfg.outcome)
    subject = cfg.id or id_col
    wide = _to_wide(df, cfg.outcome, subject, cfg.condition)
    c1, c2 = wide.columns[0], wide.columns[1]

    alt_map = {"two_sided": "two-sided", "greater": "greater", "less": "less"}
    res = pg.ttest(wide[c1], wide[c2], paired=True, alternative=alt_map[cfg.alternative])

    t = float(res["T"].iloc[0])
    dof = int(res["dof"].iloc[0])
    p = float(res["p_val"].iloc[0])
    d = float(res["cohen_d"].iloc[0])
    ci_lo, ci_hi = res["CI95"].iloc[0]

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Paired t-test: {cfg.outcome} differed between {c1} and {c2}, "
        f"t({dof}) = {t:.2f}, p {p_str}, Cohen's d_z = {d:.2f} "
        f"[95% CI: {ci_lo:.2f}, {ci_hi:.2f}]."
    )

    return AnalysisResult(
        method="Paired t-test",
        method_key="paired_t",
        primary=res,
        descriptives=_descriptives_paired(wide),
        effect_size={"cohens_dz": d},
        n_total=len(wide),
        interpretation=interpretation,
        extras={"condition_labels": [str(c1), str(c2)], "alternative": cfg.alternative},
    )


def wilcoxon(
    df: pd.DataFrame, cfg: PairedConfig, id_col: str
) -> AnalysisResult:
    df = filter_dv(df, cfg.outcome)
    subject = cfg.id or id_col
    wide = _to_wide(df, cfg.outcome, subject, cfg.condition)
    c1, c2 = wide.columns[0], wide.columns[1]

    alt_map = {"two_sided": "two-sided", "greater": "greater", "less": "less"}
    res = pg.wilcoxon(wide[c1], wide[c2], alternative=alt_map[cfg.alternative])

    w = float(res["W_val"].iloc[0])
    p = float(res["p_val"].iloc[0])
    rbc = float(res["RBC"].iloc[0])

    p_str = "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".")
    interpretation = (
        f"Wilcoxon signed-rank test: {cfg.outcome} differed between {c1} and {c2}, "
        f"W = {w:.1f}, p {p_str}, matched-pairs rank-biserial r = {rbc:.2f}."
    )

    return AnalysisResult(
        method="Wilcoxon signed-rank test",
        method_key="wilcoxon",
        primary=res,
        descriptives=_descriptives_paired(wide),
        effect_size={"rank_biserial": rbc},
        n_total=len(wide),
        interpretation=interpretation,
        extras={"condition_labels": [str(c1), str(c2)], "alternative": cfg.alternative},
    )
