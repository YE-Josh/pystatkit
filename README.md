# pystatkit

**A reproducible, human-in-the-loop statistical analysis toolkit for behavioural and health sciences research.**

![status](https://img.shields.io/badge/status-alpha%20(v0.2)-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![tests](https://img.shields.io/badge/tests-62%20passing-brightgreen)

---

## Overview

`pystatkit` is a Python toolkit that streamlines a complete statistical analysis workflow — from descriptive statistics to inferential testing, assumption checking, and APA-formatted publication-ready output — in a single configuration-driven run.

Unlike tools that attempt to fully automate statistical decision-making, `pystatkit` is built around a **human-in-the-loop** philosophy: the toolkit transparently reports assumption checks, but the researcher chooses the statistical method. This avoids a common pitfall of fully automated pipelines — silently applying an inappropriate method when assumptions are violated — while still removing the tedium of manual test execution, effect size computation, and table formatting.

A single YAML config file specifies the study design and all analyses; `pystatkit` loads the data once and runs every enabled method in sequence, producing one APA-styled report per method.

## Status

**Alpha (v0.2).** All eight core method families are implemented and tested (62 tests passing). APIs and output formats may still change before v1.0. Early feedback from the research community is warmly welcomed.

## Design Principles

1. **Human judgement over automated selection.** Assumption checks are reported transparently; the researcher chooses the method. No `auto` option exists anywhere in the config — explicit choice is required.
2. **Reproducibility by default.** Every analysis is driven by a version-controlled configuration file. Outputs are annotated with the config path, Git commit hash, data hash, and timestamps.
3. **Multi-study reusability.** One installation, one codebase, many studies — provided data follow a shared long-format schema.
4. **Publication-ready output.** APA 7 format, exported to `.docx` and `.xlsx`.
5. **Built on established libraries.** Statistics rely on `pingouin`, `tableone`, and `statsmodels` rather than re-implementing tests. `pystatkit` is an orchestration and formatting layer.

## Methods implemented in v0.2

| Method family | Methods |
|---|---|
| Demographic / Table 1 | `tableone` wrapper with per-variable tests |
| Two-group independent | Student's *t*, Welch's *t*, Mann-Whitney *U* |
| Two-group paired | Paired *t*, Wilcoxon signed-rank |
| One-way ANOVA | ANOVA + Tukey/Games-Howell, Welch's ANOVA, Kruskal-Wallis + Dunn's |
| Repeated-measures ANOVA | RM-ANOVA with Mauchly's test + GG/HF correction + pairwise post-hoc |
| Mixed ANOVA | Within × Between with simple-effects follow-up on significant interactions |
| Correlations | Pearson / Spearman / Kendall with CI, matrix output |
| ANCOVA | Covariate adjustment + assumption checks (slopes, linearity, residuals) + adjusted means |

## Installation

```bash
git clone <your-repo-url>
cd pystatkit
pip install -e .
```

With dev dependencies:

```bash
pip install -e ".[dev]"
```

## Quick start

```bash
# 1. Generate the bundled synthetic example dataset
python examples/study_example/generate_data.py

# 2. Run the full v0.2 demo (7 methods in one config)
python -m pystatkit.cli \
    --config examples/study_example/config/full_demo.yaml \
    --no-confirm
```

This produces one `.docx` + `.xlsx` per method in `examples/study_example/outputs/`, plus a shared run log. Drop `--no-confirm` for interactive confirmation after each assumption check.

## A minimal config

```yaml
study:
  name: "Study 2: VR vs real-world gait"
  analyst: "Joash Ye"
  date: "2026-04-17"

data:
  file: "data/study2.csv"
  id_col: "subject_id"
  format: "long"

defaults:
  alpha: 0.05
  confirm_method: true

output:
  dir: "results"
  basename: "study2"
  formats: ["docx", "xlsx"]

methods:
  demographic:
    enabled: true
    group_by: "group"
    continuous: ["age", "bmi"]
    categorical: ["sex"]

  two_group:
    enabled: true
    outcome: "gaze_duration"
    group: "group"
    method: "welch_t"
```

## Data schema

`pystatkit` expects **long format** — one observation per row. The config names the columns used for `outcome`, `group`, `subject`, etc. Multiple outcomes can live in separate columns of the same file; `pystatkit` filters to rows with a valid value for the outcome under analysis.

```
subject_id | group | time | age | sex | gaze_duration | rt
S01        | HC    | T1   | 68  | M   | 1.23          | 450
S01        | HC    | T2   | 68  | M   | NaN           | 475
S02        | PwP   | T1   | 71  | F   | 1.67          | 510
```

If your data is wide format, convert it to long with `pandas.melt()` before passing it to `pystatkit`.

## Reproducibility features

Every output file embeds:

- Path to the config file that produced it
- Short SHA-256 hash of the input data
- Git commit hash (and dirty-working-tree flag)
- ISO timestamp and Python/platform version
- `pystatkit` version

This means you can always trace a table in a manuscript back to the exact code, data, and config that produced it.

## Roadmap

- **v0.3** — Wide-format input support via automatic `pd.melt`; more effect sizes (omega², epsilon²)
- **v0.4** — Mixed-effects models via `statsmodels`; Bayesian alternatives
- **v0.5** — Interactive method selection with live assumption feedback (TUI)
- **v1.0** — Stable API, full documentation, reference-dataset validation suite

## Scope and limitations

`pystatkit` is intended for standard inferential analyses in experimental research designs. It is **not** a substitute for statistical expertise. Users are expected to understand the methods they select. Complex causal inference, structural equation modelling, and bespoke modelling strategies are outside scope.

Results should be cross-checked against an independent statistical package (SPSS, R, JASP) during initial adoption.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Feedback on design and scope is especially welcome at this early stage.

## License

MIT. See [`LICENSE`](LICENSE).

## Acknowledgements

`pystatkit` builds on excellent open-source work, especially:

- [`pingouin`](https://pingouin-stats.org/) — Raphael Vallat
- [`tableone`](https://github.com/tompollard/tableone) — Tom Pollard *et al.*
- [`statsmodels`](https://www.statsmodels.org/)
- [`pandas`](https://pandas.pydata.org/)
- [`python-docx`](https://python-docx.readthedocs.io/)

---

*Developed as part of PhD research in Sport and Health Sciences at the University of Exeter.*
