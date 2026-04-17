# Example: pystatkit v0.2 end-to-end demo

This folder contains a complete `pystatkit` v0.2 demonstration — one YAML config exercising 7 of the 8 supported method families.

## Quick start

From the repository root:

```bash
# 1. Generate the synthetic dataset (only needed once)
python examples/study_example/generate_data.py

# 2. Run the full demo
python -m pystatkit.cli \
    --config examples/study_example/config/full_demo.yaml \
    --no-confirm
```

Remove `--no-confirm` for the interactive human-in-the-loop experience: after each method's assumption check is displayed, you confirm before the analysis runs.

## What the demo runs

| Method | What it does | Output files |
|---|---|---|
| `demographic` | Table 1 by group, with automatic dedup of long-format repeats | `v02_demo_demographic.{docx,xlsx}` |
| `two_group` | Welch's *t*-test: HC vs PwP on gaze duration | `v02_demo_two_group.{docx,xlsx}` |
| `anova_oneway` | One-way ANOVA with Tukey: rt across 3 time points | `v02_demo_anova_oneway.{docx,xlsx}` |
| `anova_rm` | Repeated-measures ANOVA with Mauchly + GG + pairwise post-hoc | `v02_demo_anova_rm.{docx,xlsx}` |
| `anova_mixed` | Mixed ANOVA (time × group) + simple effects on significant interaction | `v02_demo_anova_mixed.{docx,xlsx}` |
| `correlation` | Spearman correlations among 5 subject-level variables | `v02_demo_correlation.{docx,xlsx}` |
| `ancova` | ANCOVA of motor score by group, adjusting for baseline cognition | `v02_demo_ancova.{docx,xlsx}` |

(`paired` is disabled in the example config to avoid redundancy with `anova_rm`, but is fully supported.)

## Synthetic dataset

The script `generate_data.py` creates `data/synthetic_v02_data.csv` with:

- **40 subjects** (20 HC, 20 PwP)
- Long format: one row per subject × time point = 120 rows
- Subject-level columns: `age`, `bmi`, `sex`, `gaze_duration`, `motor_score`, `baseline_cognition`
- Within-subject column: `rt` measured at `T1`, `T2`, `T3` (with a deliberate PwP × time interaction for the mixed-ANOVA demo)

The data uses a fixed random seed (42) so results are reproducible.

## Notes

- The data is purely synthetic and designed to produce clean, interpretable results for demonstration. It does not represent any real study population.
- For multi-DV long-format data (like this one), `pystatkit` automatically filters to rows with valid values of the outcome under analysis, and `demographic` and `correlation` deduplicate repeated rows before summarizing.
