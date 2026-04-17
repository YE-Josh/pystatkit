# pystatkit

**A reproducible, human-in-the-loop statistical analysis toolkit for behavioural and health sciences research.**

![status](https://img.shields.io/badge/status-pre--alpha-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## Overview

`pystatkit` is a Python toolkit that streamlines the statistical analysis workflow typical of empirical research in the behavioural, sport, and health sciences — from descriptive statistics to inferential testing and publication-ready tables.

Unlike tools that attempt to fully automate statistical decision-making, `pystatkit` is built around a **human-in-the-loop** philosophy: the toolkit transparently reports assumption checks and candidate methods, while the researcher retains explicit control over the choice of statistical test. This design avoids a common pitfall of fully automated pipelines — silently applying an inappropriate method when data violate assumptions — while still removing the tedium of manual test execution, effect size computation, and APA-style table formatting.

`pystatkit` is designed to serve **multiple studies from a single codebase**. A single configuration file describes the study design, dependent variables, and grouping factors; the same analysis engine can then be reused across studies without rewriting analysis scripts.

## Status

**Pre-alpha.** The project is in its initial design phase. APIs, configuration schema, and output formats are subject to substantial change. The repository is public to invite early feedback on the design and scope. A first usable release is planned; follow or star the repository for updates.

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
2. **Reproducibility by default.** Every analysis is driven by a version-controlled configuration file. Outputs are annotated with the configuration, commit hash, and input data fingerprint.
3. **Multi-study reusability.** A single installation and codebase can serve multiple studies, provided data follow a shared long-format schema.
4. **Publication-ready output.** Tables are formatted according to APA 7th edition conventions and exported to `.docx` and `.xlsx`.
5. **Built on established libraries.** Statistical computations rely on well-maintained packages (notably `pingouin`, `statsmodels`, and `tableone`) rather than re-implementing tests. `pystatkit` is an orchestration and formatting layer.

## Planned Features

The following capabilities are targeted for the first usable release:

- **Data ingestion** from `.csv` and `.xlsx` files in long format, with schema validation.
- **Descriptive (demographic) tables** via a `tableone` wrapper, with APA-styled export.
- **Assumption checks** including Shapiro–Wilk, Levene's test, and Mauchly's test of sphericity, reported in a unified format.
- **Statistical methods** covering:
  - Independent and paired *t*-tests, Welch's *t*-test
  - Mann–Whitney *U* and Wilcoxon signed-rank tests
  - One-way ANOVA, repeated-measures ANOVA, mixed ANOVA, ANCOVA
  - Kruskal–Wallis and Friedman tests
  - Post-hoc comparisons with common correction methods (Bonferroni, Holm, FDR)
  - Pearson and Spearman correlations; chi-square and Fisher's exact tests
- **Interactive method selection**, presenting assumption check results and candidate methods before execution.
- **APA 7 formatter** producing `.docx` tables ready for inclusion in manuscripts.
- **Run logging** recording configuration, Git commit hash, data hash, timestamps, and assumption check results alongside every output.

Planned for later releases: mixed-effects models (`statsmodels.MixedLM`), Bayesian alternatives, power analysis integration, and richer visualization export.

## Intended Workflow

```
┌──────────────────┐
│   config.yaml    │  Study design, variables, output preferences
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Data ingestion  │  Validation against expected long-format schema
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Assumption check │  Normality, homogeneity, sphericity — reported in full
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Method choice   │  Researcher selects; toolkit may suggest
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Analysis     │  Test + post-hoc + effect sizes
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   APA table +    │  .docx and .xlsx with full provenance metadata
│   run log        │
└──────────────────┘
```

## Installation

*Not yet available.* Installation instructions will be provided with the first tagged release. Planned distribution is via PyPI:

```bash
pip install pystatkit
```

Development installation from source will also be supported.

## Data Schema

To allow a single codebase to serve multiple studies, `pystatkit` expects input data in **long format**, with one observation per row. Required columns are specified in the study configuration file. A minimal example:

| subject_id | group | condition | age | sex | dv_1 | dv_2 |
|------------|-------|-----------|-----|-----|------|------|
| S01        | HC    | real      | 68  | M   | 1.23 | 0.045|
| S01        | HC    | VR        | 68  | M   | 1.45 | 0.052|
| S02        | PwP   | real      | 71  | F   | 1.67 | 0.061|
| …          | …     | …         | …   | …   | …    | …    |

Detailed schema requirements will accompany the first release.

## Scope and Limitations

`pystatkit` is intended for standard inferential analyses in experimental research designs. It is **not** a substitute for statistical expertise. Users are expected to understand the methods they select and to validate results against established software. Analyses involving complex causal inference, structural equation modelling, or bespoke modelling strategies are outside the current scope.

Results should be cross-checked against an independent statistical package during initial adoption.

## Roadmap

- **v0.1** — Core pipeline: config loader, long-format validator, `tableone` integration, independent/paired *t*-tests with APA export.
- **v0.2** — One-way and repeated-measures ANOVA, post-hoc comparisons, non-parametric alternatives.
- **v0.3** — Mixed ANOVA, ANCOVA, correlation and chi-square support.
- **v0.4** — Interactive method selection; provenance logging.
- **v1.0** — Stable API, full documentation, tested against reference datasets.

## Contributing

Feedback, feature requests, and discussion of the design are warmly welcomed at this early stage. Please open an issue to propose features or report problems. Contribution guidelines and a code of conduct will be added prior to the first release.

## Citation

A citation entry will be provided with the first tagged release. If you use the toolkit in preparatory work in the meantime, please cite the repository URL.

## License

Released under the MIT License. See [`LICENSE`](LICENSE) for full terms.

## Acknowledgements

`pystatkit` builds on the work of several excellent open-source projects, most notably:

- [`pingouin`](https://pingouin-stats.org/) by Raphael Vallat — statistical tests and effect sizes
- [`tableone`](https://github.com/tompollard/tableone) by Tom Pollard and colleagues — descriptive tables
- [`statsmodels`](https://www.statsmodels.org/) — regression and mixed-effects modelling
- [`pandas`](https://pandas.pydata.org/) — data manipulation

---

*Developed as part of PhD research in Sport and Health Sciences at the University of Exeter.*
