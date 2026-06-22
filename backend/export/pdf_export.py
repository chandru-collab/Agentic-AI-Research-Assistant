"""
PDF Export Module.

Converts research reports to styled PDF documents using fpdf2.
Handles Markdown-to-PDF conversion with headers, body text, and source links.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fpdf import FPDF

from backend.config import settings

logger = logging.getLogger(__name__)


class ResearchReportPDF(FPDF):
    """Custom PDF class with header/footer for research reports."""

    def __init__(self, title: str = "Research Report") -> None:
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=25)

    def header(self) -> None:
        """Render the page header."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self.report_title, align="L")
        self.cell(0, 8, "AI Research Assistant", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self) -> None:
        """Render the page footer."""
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0, 10,
            f"Page {self.page_no()}/{{nb}}",
            align="C",
        )


def _clean_text(text: str) -> str:
    """Clean text for PDF rendering — remove unsupported characters."""
    # Replace common unicode characters with ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u2026": "...",
        "\u2022": "*",
        "\u00a0": " ",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Encode to latin-1 and replace unencodable characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


def export_pdf(
    session_data: dict,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Export a research session's report as a styled PDF.

    Parameters
    ----------
    session_data : dict
        Complete session data with 'final_report', 'user_query', etc.
    output_dir : Path, optional
        Directory to save the file. Defaults to settings.REPORTS_DIR.

    Returns
    -------
    Path
        Path to the generated PDF file.
    """
    output_dir = output_dir or settings.REPORTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    session_id = session_data.get("session_id", "unknown")
    query = session_data.get("user_query", "Research")
    report = session_data.get("final_report", "No report available.")
    created_at = session_data.get(
        "created_at", datetime.now(timezone.utc).isoformat()
    )
    sources = session_data.get("sources", [])

    # Create filename
    safe_query = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_"
        for c in query[:50]
    ).strip().replace(" ", "_")

    filename = f"{safe_query}_{session_id[:8]}.pdf"
    filepath = output_dir / filename

    try:
        pdf = ResearchReportPDF(title=_clean_text(query))
        pdf.alias_nb_pages()
        pdf.add_page()

        # ── Title Page ──
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(30, 30, 80)
        pdf.ln(20)
        pdf.multi_cell(0, 12, _clean_text(query), align="C")
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, "Research Report", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.cell(0, 8, f"Generated: {created_at}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Sources: {len(sources)}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0, 8,
            f"Session: {session_id[:8]}...",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )

        pdf.ln(10)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(40, pdf.get_y(), 170, pdf.get_y())
        pdf.ln(10)

        # ── Report Body ──
        pdf.add_page()
        _render_markdown_to_pdf(pdf, report)

        # ── Save ──
        pdf.output(str(filepath))
        logger.info(f"PDF report exported to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise


def _render_markdown_to_pdf(pdf: FPDF, markdown_text: str) -> None:
    """
    Convert Markdown text to PDF content.

    Handles: # headers, **bold**, *italic*, - bullet lists,
    numbered lists, and plain paragraphs.
    """
    lines = markdown_text.split("\n")

    for line in lines:
        stripped = line.strip()

        if not stripped:
            pdf.ln(4)
            continue

        # Skip horizontal rules
        if stripped in ("---", "***", "___"):
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(6)
            continue

        # Headers
        if stripped.startswith("# "):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("# ").strip()
            _render_header(pdf, text, level)
            continue

        # Bullet points
        if stripped.startswith(("- ", "* ", "• ")):
            text = stripped[2:].strip()
            _render_bullet(pdf, text)
            continue

        # Numbered lists
        numbered_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if numbered_match:
            num = numbered_match.group(1)
            text = numbered_match.group(2)
            _render_numbered(pdf, num, text)
            continue

        # Regular paragraph
        _render_paragraph(pdf, stripped)


def _render_header(pdf: FPDF, text: str, level: int) -> None:
    """Render a header at the given level."""
    sizes = {1: 18, 2: 15, 3: 13, 4: 12, 5: 11, 6: 10}
    size = sizes.get(level, 10)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", size)
    pdf.set_text_color(30, 30, 80)
    pdf.multi_cell(0, size * 0.6, _clean_text(text))
    pdf.ln(2)

    # Reset
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)


def _render_bullet(pdf: FPDF, text: str) -> None:
    """Render a bullet point."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    x = pdf.get_x()
    pdf.cell(8, 5, chr(149))  # bullet character
    pdf.multi_cell(0, 5, _clean_text(text))
    pdf.ln(1)


def _render_numbered(pdf: FPDF, num: str, text: str) -> None:
    """Render a numbered list item."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(10, 5, f"{num}.")
    pdf.multi_cell(0, 5, _clean_text(text))
    pdf.ln(1)


def _render_paragraph(pdf: FPDF, text: str) -> None:
    """Render a paragraph of text."""
    # Handle bold (**text**) and italic (*text*)
    clean = _clean_text(text)
    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", clean)  # Remove bold markers
    clean = re.sub(r"\*(.*?)\*", r"\1", clean)  # Remove italic markers
    clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)  # Remove link syntax

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, clean)
    pdf.ln(2)


def get_pdf_bytes(session_data: dict) -> bytes:
    """
    Generate PDF content as bytes (for download without saving to disk).

    Parameters
    ----------
    session_data : dict
        Complete session data.

    Returns
    -------
    bytes
        PDF file content.
    """
    query = session_data.get("user_query", "Research")
    report = session_data.get("final_report", "No report available.")
    session_id = session_data.get("session_id", "unknown")
    created_at = session_data.get(
        "created_at", datetime.now(timezone.utc).isoformat()
    )
    sources = session_data.get("sources", [])

    pdf = ResearchReportPDF(title=_clean_text(query))
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 30, 80)
    pdf.ln(15)
    pdf.multi_cell(0, 11, _clean_text(query), align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Generated: {created_at}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Sources: {len(sources)}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.add_page()
    _render_markdown_to_pdf(pdf, report)

    return bytes(pdf.output())
