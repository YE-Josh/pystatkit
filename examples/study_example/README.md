# Example: pystatkit v0.1 end-to-end

This folder demonstrates a complete `pystatkit` workflow using synthetic data modelled after a gait-and-gaze study comparing healthy controls (HC) and people with Parkinson's disease (PwP).

## Quick start

From the repository root:

```bash
# 1. Generate the synthetic dataset (only needed once)
python examples/study_example/generate_data.py

# 2. Run each of the three example analyses
python -m pystatkit.cli --config examples/study_example/config/01_two_group.yaml --no-confirm
python -m pystatkit.cli --config examples/study_example/config/02_paired.yaml    --no-confirm
python -m pystatkit.cli --config examples/study_example/config/03_anova.yaml     --no-confirm
```

Remove the `--no-confirm` flag to see the human-in-the-loop prompt: assumption checks are displayed and you confirm the method before analysis runs.

## Three demonstrated designs

| # | Config | Design | Method | What it shows |
|---|---|---|---|---|
| 1 | `01_two_group.yaml` | two-group independent | Welch's *t* | HC vs PwP gaze duration |
| 2 | `02_paired.yaml`    | two-group paired      | paired *t*  | pre vs post step variability |
| 3 | `03_anova.yaml`     | one-way ANOVA         | ANOVA + Tukey | RT across three difficulty levels |

## What each run produces

For each config, `pystatkit` writes three files to `outputs/`:

- `<name>.docx` — APA-styled report, ready to paste into a manuscript
- `<name>.xlsx` — multi-sheet workbook (Summary, Descriptives, Primary, PostHoc)
- `logs/<name>.log` — run log with provenance metadata

## Data schema

The synthetic dataset `data/synthetic_gait_data.csv` is in long format:

| Column | Description |
|---|---|
| `subject_id` | Unique subject identifier |
| `group` | HC or PwP |
| `condition` | Session label (baseline / pre / post / trial) |
| `difficulty` | Trial difficulty (easy / medium / hard / NA) |
| `gaze_duration_real` | Gaze duration DV (one row per subject) |
| `step_variability` | Step variability DV (pre/post — two rows per subject) |
| `reaction_time` | Reaction time DV (three rows per subject × difficulty) |

Each DV lives in its own column; non-applicable rows for that DV are `NaN`. `pystatkit` filters to rows with a valid DV before running analyses.

## Notes

The data are purely synthetic and generated with a fixed random seed (`42`) in `generate_data.py`. They are designed to produce clean, interpretable results for demonstration — not to reflect any specific real study.
