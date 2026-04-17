# pystatkit

**A reproducible, human-in-the-loop statistical analysis toolkit for behavioural and health sciences research.**

![status](https://img.shields.io/badge/status-alpha%20(v0.1)-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## Overview

`pystatkit` is a Python toolkit that streamlines the statistical analysis workflow typical of empirical research in the behavioural, sport, and health sciences — from descriptive statistics to inferential testing and publication-ready tables.

Unlike tools that attempt to fully automate statistical decision-making, `pystatkit` is built around a **human-in-the-loop** philosophy: the toolkit transparently reports assumption checks and candidate methods, while the researcher retains explicit control over the choice of statistical test. This design avoids a common pitfall of fully automated pipelines — silently applying an inappropriate method when data violate assumptions — while still removing the tedium of manual test execution, effect size computation, and APA-style table formatting.

`pystatkit` is designed to serve **multiple studies from a single codebase**. A single configuration file describes the study design, dependent variables, and grouping factors; the same analysis engine can then be reused across studies without rewriting analysis scripts.

## Status

**Alpha (v0.1).** Core pipeline and a focused set of statistical methods are implemented and tested. APIs and output formats may still change. Early feedback from the research community is warmly welcomed.

## Motivation

Researchers running multi-study projects often face the same workflow repeatedly:

1. Load a cleaned dataset.
2. Check statistical assumptions (normality, homogeneity of variance, sphericity).
3. Select an appropriate test based on the design and assumption check outcomes.
4. Run the test together with relevant post-hoc comparisons and effect sizes.
5. Format the output as a publication-ready table.

Existing tools address parts of this workflow well — for example, `tableone` for descriptive tables and `pingouin` for statistical tests — but a gap remains for a reproducible, configuration-driven layer that connects these steps, handles multiple studies uniformly, and produces APA-style output. Point-and-click tools such as SPSS, JASP, and jamovi offer usability but limit reproducibility and integration with version control. `pystatkit` aims to fill this gap for Python-based research workflows.

## Design Principles

1. **Human judgement over automated selection.** Assumption checks are reported transparently; the researcher chooses the statistical method. The toolkit may suggest candidate methods but never silently selects one.
2. **Reproducibility by default.** Every analysis is driven by a version-controlled configuration file. Outputs are annotated with the configuration, Git commit hash, and input data hash.
3. **Multi-study reusability.** A single installation and codebase can serve multiple studies, provided data follow a shared long-format schema.
4. **Publication-ready output.** Tables are formatted according to APA 7th edition conventions and exported to `.docx` and `.xlsx`.
5. **Built on established libraries.** Statistical computations rely on well-maintained packages (notably `pingouin`) rather than re-implementing tests. `pystatkit` is an orchestration and formatting layer.

## What's in v0.1

**Designs and methods:**

| Design | Methods |
|---|---|
| Two-group independent | Student's *t*, Welch's *t*, Mann–Whitney *U* |
| Two-group paired      | Paired *t*, Wilcoxon signed-rank |
| One-way ANOVA         | ANOVA + Tukey / Games–Howell, Kruskal–Wallis + Dunn's |

**Infrastructure:**

- YAML configuration schema with validation
- Long-format data loader (`.csv` / `.xlsx`) with schema checks
- Assumption checks: Shapiro–Wilk normality, Levene's homogeneity of variance
- Interactive confirmation after assumption review (`--no-confirm` for scripting)
- APA 7 formatter → `.docx` (paste-into-manuscript) + `.xlsx` (multi-sheet archive)
- Run provenance: Git commit hash, data hash, timestamps, full config echoed in outputs
- 20 unit tests validating outputs against direct `pingouin` calls

## Installation

```bash
git clone <your-repo-url>
cd pystatkit
pip install -e .
```

Development install with test tools:

```bash
pip install -e ".[dev]"
```

## Quick start

```bash
# 1. Generate the bundled synthetic example dataset
python examples/study_example/generate_data.py

# 2. Run a Welch's t-test from its config
python -m pystatkit.cli \
    --config examples/study_example/config/01_two_group.yaml \
    --no-confirm
```

This produces `01_gaze_duration_HC_vs_PwP.docx` and `.xlsx` in `examples/study_example/outputs/`, along with a log file containing full provenance metadata.

For an interactive run with the human-in-the-loop prompt, drop the `--no-confirm` flag.

See `examples/study_example/README.md` for the full three-analysis walkthrough.

## Minimal config example

```yaml
data_file: data/study2.csv
design: two_group_independent
method: welch_t

dv: gaze_duration
group: group            # e.g. HC / PwP

output_dir: outputs/tables
output_name: study2_gaze_HC_vs_PwP
alpha: 0.05
confirm_method: true
```

## Data schema

To let one codebase serve many studies, `pystatkit` expects long-format data — one observation per row. The config file names the columns used for `dv`, `group`, `subject`, and `condition` as appropriate to the design.

| subject_id | group | condition | age | sex | dv_1 | dv_2 |
|------------|-------|-----------|-----|-----|------|------|
| S01        | HC    | real      | 68  | M   | 1.23 | 0.045|
| S01        | HC    | VR        | 68  | M   | 1.45 | 0.052|
| S02        | PwP   | real      | 71  | F   | 1.67 | 0.061|

Multiple DVs can live as separate columns in the same file; `pystatkit` filters to rows with a valid value for the DV under analysis.

## Roadmap

- **v0.2** — Demographic (Table 1) generation via `tableone`; one-sample tests; richer non-parametric options
- **v0.3** — Repeated-measures ANOVA, mixed ANOVA, ANCOVA
- **v0.4** — Correlations (Pearson / Spearman), chi-square, Fisher's exact
- **v0.5** — Interactive method selection with live assumption feedback
- **v1.0** — Stable API, full documentation, reference-dataset validation suite

## Scope and limitations

`pystatkit` is intended for standard inferential analyses in experimental research designs. It is **not** a substitute for statistical expertise. Users are expected to understand the methods they select and to validate results against established software during initial adoption.

Analyses involving complex causal inference, structural equation modelling, or bespoke modelling strategies are outside the current scope.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Feedback, feature requests, and design discussion are especially welcome at this early stage.

## License

Released under the MIT License. See [`LICENSE`](LICENSE) for full terms.

## Acknowledgements

`pystatkit` builds on the work of several excellent open-source projects:

- [`pingouin`](https://pingouin-stats.org/) by Raphael Vallat — statistical tests and effect sizes
- [`statsmodels`](https://www.statsmodels.org/) — regression and mixed-effects modelling (planned)
- [`pandas`](https://pandas.pydata.org/) — data manipulation
- [`python-docx`](https://python-docx.readthedocs.io/) — Word output

---

*Developed as part of PhD research in Sport and Health Sciences at the University of Exeter.*
