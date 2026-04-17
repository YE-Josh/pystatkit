"""Generate synthetic data that exercises all v0.2 methods.

Design:
- 40 subjects: 20 HC, 20 PwP
- Each subject has demographic columns (age, bmi, sex)
- Each subject has a one-row-per-subject outcome (gaze_duration, motor_score)
- Each subject has 3 repeated measurements across time (rt at T1/T2/T3)
- PwP shows a stronger time effect (interaction for mixed ANOVA)

Columns:
  subject_id, group, time, age, bmi, sex,
  gaze_duration, motor_score, baseline_cognition, rt
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate(out_path: Path, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    n_hc, n_pwp = 20, 20

    subjects_hc = [f"HC{i:02d}" for i in range(n_hc)]
    subjects_pwp = [f"PD{i:02d}" for i in range(n_pwp)]
    all_subjects = subjects_hc + subjects_pwp
    groups = ["HC"] * n_hc + ["PwP"] * n_pwp

    age = rng.normal(68, 8, len(all_subjects))
    bmi = rng.normal(26, 4, len(all_subjects))
    sex = rng.choice(["M", "F"], len(all_subjects))
    baseline_cog = rng.normal(90, 12, len(all_subjects))

    # Subject-level DVs.
    gaze_hc = rng.normal(1.20, 0.25, n_hc)
    gaze_pwp = rng.normal(1.55, 0.35, n_pwp)
    gaze = np.concatenate([gaze_hc, gaze_pwp])

    motor_hc = rng.normal(40, 10, n_hc)
    motor_pwp = rng.normal(55, 13, n_pwp)
    # Make motor correlate with baseline cognition.
    motor = np.concatenate([motor_hc, motor_pwp]) + 0.2 * baseline_cog

    # Build long-format rows with 3 time points for rt.
    rows = []
    for sub, grp, a, b, s, g, m, bc in zip(
        all_subjects, groups, age, bmi, sex, gaze, motor, baseline_cog
    ):
        for t, offset in [("T1", 0), ("T2", 30), ("T3", 60)]:
            # PwP has stronger time effect → interaction.
            t_effect = offset * (1.6 if grp == "PwP" else 1.0)
            rt = 450 + t_effect + rng.normal(0, 25)
            rows.append(
                {
                    "subject_id": sub,
                    "group": grp,
                    "time": t,
                    "age": a,
                    "bmi": b,
                    "sex": s,
                    "gaze_duration": g,
                    "motor_score": m,
                    "baseline_cognition": bc,
                    "rt": rt,
                }
            )

    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows ({df['subject_id'].nunique()} subjects) to {out_path}")


if __name__ == "__main__":
    generate(Path(__file__).parent / "data" / "synthetic_v02_data.csv")
