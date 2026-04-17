"""Generate synthetic HC vs PwP-style data for demonstrating pystatkit.

Creates a long-format CSV with three dependent variables suitable for
the three v0.1 designs:

- gaze_duration_real : DV for two-group independent (HC vs PwP)
- step_variability   : DV measured pre/post for paired analysis
- reaction_time      : DV across three difficulty levels for ANOVA

This is synthetic data for demonstration only — it does not represent
real participants.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate(out_path: Path, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)

    n_hc, n_pwp = 22, 20
    subjects_hc = [f"HC{i:02d}" for i in range(n_hc)]
    subjects_pwp = [f"PD{i:02d}" for i in range(n_pwp)]
    all_subjects = subjects_hc + subjects_pwp
    groups = ["HC"] * n_hc + ["PwP"] * n_pwp

    # DV 1: gaze_duration_real (HC shorter, PwP longer) — for two-group test.
    gaze_hc = rng.normal(loc=1.20, scale=0.25, size=n_hc)
    gaze_pwp = rng.normal(loc=1.55, scale=0.35, size=n_pwp)  # unequal variance
    gaze_duration_real = np.concatenate([gaze_hc, gaze_pwp])

    # DV 2: step_variability measured pre/post — for paired test.
    # All subjects measured twice; post slightly higher.
    pre = rng.normal(loc=0.045, scale=0.010, size=len(all_subjects))
    post = pre + rng.normal(loc=0.006, scale=0.004, size=len(all_subjects))

    # DV 3: reaction_time across three difficulty levels — for one-way ANOVA.
    # Same subjects measured under three conditions, but we'll present it as
    # independent for a simple one-way ANOVA demo.
    rt_easy = rng.normal(loc=450, scale=60, size=len(all_subjects))
    rt_medium = rng.normal(loc=520, scale=70, size=len(all_subjects))
    rt_hard = rng.normal(loc=620, scale=90, size=len(all_subjects))

    # Build long-format rows.
    rows = []

    # Gaze duration: one row per subject (independent design uses this column).
    for sub, grp, g in zip(all_subjects, groups, gaze_duration_real):
        rows.append(
            {
                "subject_id": sub,
                "group": grp,
                "condition": "baseline",
                "difficulty": "NA",
                "gaze_duration_real": g,
                "step_variability": np.nan,
                "reaction_time": np.nan,
            }
        )

    # Step variability pre/post: two rows per subject.
    for sub, grp, p_val, q_val in zip(all_subjects, groups, pre, post):
        rows.append(
            {
                "subject_id": sub,
                "group": grp,
                "condition": "pre",
                "difficulty": "NA",
                "gaze_duration_real": np.nan,
                "step_variability": p_val,
                "reaction_time": np.nan,
            }
        )
        rows.append(
            {
                "subject_id": sub,
                "group": grp,
                "condition": "post",
                "difficulty": "NA",
                "gaze_duration_real": np.nan,
                "step_variability": q_val,
                "reaction_time": np.nan,
            }
        )

    # Reaction time across difficulty: three rows per subject.
    for sub, grp, easy, med, hard in zip(
        all_subjects, groups, rt_easy, rt_medium, rt_hard
    ):
        for diff, val in [("easy", easy), ("medium", med), ("hard", hard)]:
            rows.append(
                {
                    "subject_id": sub,
                    "group": grp,
                    "condition": "trial",
                    "difficulty": diff,
                    "gaze_duration_real": np.nan,
                    "step_variability": np.nan,
                    "reaction_time": val,
                }
            )

    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    generate(Path(__file__).parent / "data" / "synthetic_gait_data.csv")
