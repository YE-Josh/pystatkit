# Changelog

All notable changes to this project are documented here.

## [0.2.0] — 2026-04-17

### Added
- **Hierarchical YAML config** with `study`, `data`, `defaults`, `output`, `methods` sections. One config can now enable multiple methods; the orchestrator runs them in the order they appear.
- **Demographic table** method via `tableone` wrapper. Auto-dedupes repeated rows per subject common in long-format data.
- **Welch's ANOVA** as a method option under `anova_oneway`.
- **Repeated-measures ANOVA** (`anova_rm`) with Mauchly's test of sphericity and Greenhouse-Geisser / Huynh-Feldt correction. Supports multi-factor within designs.
- **Mixed ANOVA** (`anova_mixed`): one within × one between factor, with automatic simple-effects follow-up on significant interactions.
- **Correlations** (`correlation`): Pearson, Spearman, and Kendall with confidence intervals and a correlation matrix output. Auto-dedupes duplicate rows across the selected variables to avoid inflated *n* in long-format data.
- **ANCOVA** (`ancova`): covariate adjustment with four configurable assumption checks (homogeneity of slopes, linearity, residual normality, residual variance homogeneity) plus adjusted (estimated marginal) means.
- **Orchestrator** (`pystatkit.core.orchestrator`) — runs all enabled methods, handles per-method column validation, assumption reporting, and graceful error handling.
- **Expanded APA formatter** with method-specific auxiliary tables (correlation matrix, adjusted means, simple effects, ANCOVA assumption sheets).
- **Study metadata block** (`study: {name, analyst, date, notes}`) written into every output for provenance.
- **Output configuration**: choose output formats (`docx`, `xlsx`, `csv` subset) and destination directory per run.

### Changed
- Removed all `method: "auto"` options from the config schema. Explicit method choice is now required — this enforces the human-in-the-loop design principle at the config level.
- `normality_check` options: dropped KS (inappropriate when parameters are estimated from data); added Anderson-Darling.
- `homogeneity_check` options: replaced Bartlett's test (too sensitive to non-normality) with mean-centered and median-centered Levene (Brown-Forsythe).
- Default `p_adjust` is now `holm` rather than `bonferroni` (Holm uniformly dominates Bonferroni).
- Data is now loaded once per run and shared across all methods, rather than re-loaded per method.
- Correlation now requires `vars` (a list); the alternative `x`/`y` style from early drafts was removed.

### Fixed
- Assumption checks and the `n_groups` schema validation now respect DV-level NaN filtering — multi-DV datasets no longer break Levene with NaN-inflated groups.

### Testing
- 62 tests, all passing. Each method has a direct comparison against a reference `pingouin` call to guard against wrapper drift.

## [0.1.0] — 2026-04-17

### Added
- Initial release. Core pipeline: YAML config → data load → assumption check → method dispatch → APA output.
- Two-group independent (Student's *t*, Welch's *t*, Mann-Whitney *U*).
- Two-group paired (paired *t*, Wilcoxon signed-rank).
- One-way ANOVA with Tukey / Games-Howell / none post-hoc, plus Kruskal-Wallis.
- Shapiro-Wilk normality, Levene's homogeneity of variance.
- APA formatter to `.docx` and `.xlsx`.
- Run provenance (Git commit hash, data hash, timestamps).
- 20 tests, all validated against direct `pingouin` calls.
