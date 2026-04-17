"""Output formatters: APA-styled tables in .docx and .xlsx."""

from pystatkit.io.apa_formatter import (
    format_p_value,
    write_docx_report,
    write_xlsx_report,
)

__all__ = ["format_p_value", "write_docx_report", "write_xlsx_report"]
