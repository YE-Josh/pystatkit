"""APA 7th edition formatting for statistical output.

Produces publication-ready tables in .docx (for direct pasting into
manuscripts) and .xlsx (for archival and further processing).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document
from docx.shared import Pt

from pystatkit.core.provenance import RunMetadata
from pystatkit.core.results import AnalysisResult


def format_p_value(p: float) -> str:
    """APA p-value formatting: 'p < .001' or 'p = .03' (no leading zero)."""
    if p < 0.001:
        return "< .001"
    return f"= {p:.3f}".replace("0.", ".")


def _round_df(df: pd.DataFrame, decimals: int = 3) -> pd.DataFrame:
    """Round numeric columns without mangling non-numeric ones."""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].round(decimals)
    return out


def write_xlsx_report(
    result: AnalysisResult,
    metadata: RunMetadata,
    output_path: str | Path,
) -> Path:
    """Write the full analysis to a multi-sheet .xlsx file.

    Sheets
    ------
    - Summary: interpretation sentence + metadata
    - Descriptives: group-wise summary statistics
    - Primary: main test results
    - Post-hoc: pairwise comparisons (if applicable)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Summary sheet.
        summary_rows = [
            ("Method", result.method),
            ("n (total)", result.n_total),
            ("Interpretation", result.interpretation),
            ("", ""),
            ("--- Run metadata ---", ""),
            *[(k, str(v)) for k, v in metadata.to_dict().items()],
        ]
        pd.DataFrame(summary_rows, columns=["Field", "Value"]).to_excel(
            writer, sheet_name="Summary", index=False
        )

        if result.descriptives is not None:
            _round_df(result.descriptives).to_excel(writer, sheet_name="Descriptives")

        _round_df(result.primary).to_excel(writer, sheet_name="Primary", index=False)

        if result.posthoc is not None:
            _round_df(result.posthoc).to_excel(
                writer, sheet_name="PostHoc", index=False
            )

    return output_path


def _add_dataframe_table(doc: Document, df: pd.DataFrame, title: str) -> None:
    """Append a titled table rendered from a DataFrame to a docx Document."""
    doc.add_heading(title, level=2)
    df_disp = _round_df(df.reset_index() if df.index.name else df)

    table = doc.add_table(rows=1, cols=len(df_disp.columns))
    table.style = "Light Grid Accent 1"

    hdr = table.rows[0].cells
    for i, col in enumerate(df_disp.columns):
        hdr[i].text = str(col)
        for run in hdr[i].paragraphs[0].runs:
            run.bold = True

    for _, row in df_disp.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)


def write_docx_report(
    result: AnalysisResult,
    metadata: RunMetadata,
    output_path: str | Path,
) -> Path:
    """Write an APA-styled .docx report.

    The document contains the interpretation sentence (ready to paste into a
    manuscript), descriptive statistics, the primary test table, and post-hoc
    comparisons if applicable. A metadata footer records provenance.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()

    # Set a clean default font.
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    doc.add_heading("Statistical Analysis Report", level=1)

    # Interpretation sentence (the APA-ready result line).
    doc.add_heading("Result", level=2)
    p = doc.add_paragraph(result.interpretation)
    p.paragraph_format.space_after = Pt(12)

    # Descriptives.
    if result.descriptives is not None:
        _add_dataframe_table(doc, result.descriptives, "Descriptive Statistics")

    # Primary test.
    _add_dataframe_table(doc, result.primary, "Primary Test Statistics")

    # Post-hoc (if present).
    if result.posthoc is not None:
        posthoc_name = result.extras.get("posthoc_method", "post-hoc")
        _add_dataframe_table(
            doc, result.posthoc, f"Post-hoc Comparisons ({posthoc_name})"
        )

    # Provenance footer.
    doc.add_heading("Run Metadata", level=2)
    for k, v in metadata.to_dict().items():
        doc.add_paragraph(f"{k}: {v}", style="List Bullet")

    doc.save(output_path)
    return output_path
