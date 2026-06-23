"""
PDF Export Module — Premium Infographic-Style Reports.

Converts research reports to visually rich PDF documents using fpdf2.
Features:
  - Gradient cover page with stat cards
  - Colored section cards with accent bars & numbered badges
  - Auto-parsed markdown tables with zebra striping
  - Styled bullet points & numbered lists with colored badges
  - Blockquotes, code blocks, inline bold/italic/link rendering
  - Sources appendix with alternating row backgrounds
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fpdf import FPDF

from backend.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Color Palette
# ═══════════════════════════════════════════════════════════

class Colors:
    """Centralized color palette for the report theme."""

    # Cover page gradient stops (navy → purple)
    GRADIENT_START = (30, 30, 80)       # #1E1E50
    GRADIENT_END = (74, 45, 122)        # #4A2D7A

    # Section accent colors (rotate per section)
    ACCENTS = [
        (79, 70, 229),    # Indigo
        (20, 184, 166),   # Teal
        (245, 158, 11),   # Amber
        (244, 63, 94),    # Rose
        (16, 185, 129),   # Emerald
        (139, 92, 246),   # Violet
    ]

    # Stat card backgrounds
    STAT_BG_1 = (238, 242, 255)   # Light indigo
    STAT_BG_2 = (204, 251, 241)   # Light teal
    STAT_BG_3 = (254, 243, 199)   # Light amber
    STAT_BG_4 = (237, 233, 254)   # Light violet

    # Text
    TITLE_WHITE = (255, 255, 255)
    HEADING_DARK = (30, 30, 80)
    BODY_TEXT = (50, 50, 60)
    BODY_LIGHT = (100, 100, 110)
    LINK_BLUE = (37, 99, 235)

    # Backgrounds
    CARD_BG = (248, 249, 252)
    TABLE_HEADER_BG = (30, 30, 80)
    TABLE_HEADER_TEXT = (255, 255, 255)
    TABLE_ZEBRA_LIGHT = (248, 249, 252)
    TABLE_ZEBRA_WHITE = (255, 255, 255)
    BLOCKQUOTE_BG = (243, 244, 246)
    CODE_BG = (39, 39, 42)
    CODE_TEXT = (228, 228, 231)

    # Decorative
    DIVIDER = (209, 213, 219)
    FOOTER_TEXT = (156, 163, 175)
    HEADER_TEXT = (107, 114, 128)


# ═══════════════════════════════════════════════════════════
# PDF Class
# ═══════════════════════════════════════════════════════════

class ResearchReportPDF(FPDF):
    """Custom PDF class with premium header/footer for research reports."""

    def __init__(self, title: str = "Research Report") -> None:
        super().__init__()
        self.report_title = title
        self.report_date = ""
        self.set_auto_page_break(auto=True, margin=28)

    def header(self) -> None:
        """Render the page header with title and branding."""
        if self.page_no() == 1:
            return  # Cover page has its own layout

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*Colors.HEADER_TEXT)

        # Left: report title (truncated)
        title_display = self.report_title[:60]
        if len(self.report_title) > 60:
            title_display += "..."
        self.cell(95, 6, _clean(title_display), align="L")

        # Right: branding
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*Colors.ACCENTS[0])
        self.cell(95, 6, "AI Research Assistant", align="R",
                  new_x="LMARGIN", new_y="NEXT")

        # Separator line
        self.set_draw_color(*Colors.DIVIDER)
        self.set_line_width(0.3)
        self.line(10, self.get_y() + 1, 200, self.get_y() + 1)
        self.ln(6)

    def footer(self) -> None:
        """Render the page footer with page number and timestamp."""
        self.set_y(-18)
        self.set_draw_color(*Colors.DIVIDER)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

        self.set_font("Helvetica", "", 7)
        self.set_text_color(*Colors.FOOTER_TEXT)
        self.cell(95, 5, self.report_date, align="L")
        self.cell(95, 5, f"Page {self.page_no()} of {{nb}}", align="R")


# ═══════════════════════════════════════════════════════════
# Text Utilities
# ═══════════════════════════════════════════════════════════

def _clean(text: str) -> str:
    """Clean text for PDF rendering — replace unsupported unicode."""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u2026": "...",
        "\u2022": "*",
        "\u00a0": " ",
        "\u2192": "->",
        "\u2190": "<-",
        "\u2715": "x",
        "\u2713": "v",
        "\u2714": "v",
        "\u2716": "x",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _draw_rounded_rect(pdf: FPDF, x: float, y: float,
                        w: float, h: float, r: float,
                        style: str = "F") -> None:
    """Draw a rectangle with rounded corners.

    Parameters
    ----------
    style : str
        'F' = filled, 'D' = draw outline, 'DF' = both.
    """
    # Clamp radius
    r = min(r, w / 2, h / 2)

    # Four straight sides
    pdf.set_x(x)
    pdf.set_y(y)

    # Use arcs for corners and lines for sides
    # Top side
    pdf.line(x + r, y, x + w - r, y)
    # Right side
    pdf.line(x + w, y + r, x + w, y + h - r)
    # Bottom side
    pdf.line(x + r, y + h, x + w - r, y + h)
    # Left side
    pdf.line(x, y + r, x, y + h - r)

    # For filled rounded rects, use a simpler approach:
    # draw filled rect + circles at corners
    if "F" in style:
        # Main body rectangles (cross shape)
        pdf.rect(x + r, y, w - 2 * r, h, "F")
        pdf.rect(x, y + r, w, h - 2 * r, "F")
        # Corner circles
        pdf.ellipse(x, y, 2 * r, 2 * r, "F")
        pdf.ellipse(x + w - 2 * r, y, 2 * r, 2 * r, "F")
        pdf.ellipse(x, y + h - 2 * r, 2 * r, 2 * r, "F")
        pdf.ellipse(x + w - 2 * r, y + h - 2 * r, 2 * r, 2 * r, "F")


def _draw_circle(pdf: FPDF, cx: float, cy: float, radius: float,
                  style: str = "F") -> None:
    """Draw a circle centered at (cx, cy)."""
    pdf.ellipse(cx - radius, cy - radius, radius * 2, radius * 2, style)


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linear interpolation between two RGB colors."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ═══════════════════════════════════════════════════════════
# Cover Page
# ═══════════════════════════════════════════════════════════

def _render_cover_page(pdf: ResearchReportPDF, session_data: dict) -> None:
    """Render the premium cover page with gradient banner and stat cards."""

    query = session_data.get("user_query", "Research Report")
    created_at = session_data.get(
        "created_at", datetime.now(timezone.utc).isoformat()
    )
    sources = session_data.get("sources", [])
    report_text = session_data.get("final_report", "")
    word_count = len(report_text.split())
    insights = session_data.get("insights", [])

    # ── Gradient Banner ──
    banner_h = 90
    steps = 40
    strip_h = banner_h / steps

    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0
        color = _lerp_color(Colors.GRADIENT_START, Colors.GRADIENT_END, t)
        pdf.set_fill_color(*color)
        pdf.rect(0, i * strip_h, 210, strip_h + 1, "F")

    # Title on banner
    pdf.set_y(25)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*Colors.TITLE_WHITE)
    pdf.multi_cell(0, 13, _clean(query), align="C")

    # Subtitle
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(200, 200, 230)
    pdf.cell(0, 8, "AI Research Report", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # ── Stat Cards (2x2 grid) ──
    pdf.set_y(banner_h + 12)

    cards = [
        (str(len(sources)), "Sources Found", Colors.STAT_BG_1, Colors.ACCENTS[0]),
        (str(len(insights)), "Key Insights", Colors.STAT_BG_2, Colors.ACCENTS[1]),
        (f"{word_count:,}", "Total Words", Colors.STAT_BG_3, Colors.ACCENTS[2]),
        (created_at[:10], "Generated", Colors.STAT_BG_4, Colors.ACCENTS[5]),
    ]

    card_w = 43
    card_h = 32
    gap = 4
    start_x = (210 - (4 * card_w + 3 * gap)) / 2

    card_y = pdf.get_y()
    for idx, (value, label, bg, accent) in enumerate(cards):
        x = start_x + idx * (card_w + gap)
        y = card_y

        # Card background
        pdf.set_fill_color(*bg)
        _draw_rounded_rect(pdf, x, y, card_w, card_h, 4, "F")

        # Accent top bar
        pdf.set_fill_color(*accent)
        pdf.rect(x, y, card_w, 3, "F")

        # Value
        pdf.set_xy(x, y + 6)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*accent)
        pdf.cell(card_w, 8, _clean(value), align="C")

        # Label
        pdf.set_xy(x, y + 16)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*Colors.BODY_LIGHT)
        pdf.cell(card_w, 6, _clean(label), align="C")

    # ── Session Info ──
    pdf.set_y(card_y + card_h + 15)

    session_id = session_data.get("session_id", "unknown")

    pdf.set_draw_color(*Colors.DIVIDER)
    pdf.set_line_width(0.5)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*Colors.BODY_LIGHT)
    pdf.cell(0, 6, f"Session ID: {session_id}", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated: {created_at}", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # ── Table of Contents placeholder ──
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*Colors.HEADING_DARK)
    pdf.cell(0, 8, "Report Contents", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Extract section headings from the report
    sections = re.findall(r"^##\s+(.+)$", report_text, re.MULTILINE)
    if sections:
        for i, section in enumerate(sections[:12], 1):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*Colors.BODY_TEXT)

            # Section number circle
            cx = 65
            cy = pdf.get_y() + 3
            pdf.set_fill_color(*Colors.ACCENTS[i % len(Colors.ACCENTS)])
            _draw_circle(pdf, cx, cy, 3, "F")
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*Colors.TITLE_WHITE)
            pdf.set_xy(cx - 3, cy - 2.5)
            pdf.cell(6, 5, str(i), align="C")

            # Section title
            pdf.set_xy(72, cy - 3)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*Colors.BODY_TEXT)
            pdf.cell(0, 6, _clean(section[:60]))
            pdf.ln(8)


# ═══════════════════════════════════════════════════════════
# Markdown Parser
# ═══════════════════════════════════════════════════════════

def _parse_markdown_blocks(text: str) -> list[dict]:
    """Parse markdown text into structured blocks.

    Returns a list of dicts with 'type' and 'content' keys.
    Types: heading, bullet, sub_bullet, numbered, paragraph,
           table, blockquote, code_block, hr
    """
    blocks = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Code block (fenced)
        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({"type": "code_block", "content": "\n".join(code_lines)})
            i += 1  # skip closing ```
            continue

        # Table detection (line with pipes)
        if "|" in stripped and stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and "|" in lines[i].strip():
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append({"type": "table", "content": table_lines})
            continue

        # Headers (# to ######)
        header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if header_match:
            level = len(header_match.group(1))
            blocks.append({
                "type": "heading",
                "level": level,
                "content": header_match.group(2).strip(),
            })
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            blocks.append({
                "type": "blockquote",
                "content": " ".join(quote_lines),
            })
            continue

        # Sub-bullet (indented)
        if re.match(r"^\s{2,}[-*]\s+", line):
            text_content = re.sub(r"^\s+[-*]\s+", "", line)
            blocks.append({"type": "sub_bullet", "content": text_content.strip()})
            i += 1
            continue

        # Bullet point
        if stripped.startswith(("- ", "* ", "• ")):
            blocks.append({"type": "bullet", "content": stripped[2:].strip()})
            i += 1
            continue

        # Numbered list
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            blocks.append({
                "type": "numbered",
                "num": num_match.group(1),
                "content": num_match.group(2).strip(),
            })
            i += 1
            continue

        # Regular paragraph
        blocks.append({"type": "paragraph", "content": stripped})
        i += 1

    return blocks


# ═══════════════════════════════════════════════════════════
# Inline Text Rendering
# ═══════════════════════════════════════════════════════════

def _render_rich_text(pdf: FPDF, text: str, max_w: float = 0,
                       line_h: float = 5) -> None:
    """Render text with inline bold, italic, and link formatting.

    Parses **bold**, *italic*, and [text](url) markers and renders
    each span with the appropriate font style using FPDF.write().
    """
    # Tokenize into spans: (style, text, url_or_None)
    spans = _parse_inline_spans(text)

    for style, span_text, url in spans:
        clean_text = _clean(span_text)
        if not clean_text:
            continue

        # Set font style
        if style == "bold":
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*Colors.BODY_TEXT)
        elif style == "italic":
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(*Colors.BODY_LIGHT)
        elif style == "bold_italic":
            pdf.set_font("Helvetica", "BI", 10)
            pdf.set_text_color(*Colors.BODY_TEXT)
        elif style == "link":
            pdf.set_font("Helvetica", "U", 10)
            pdf.set_text_color(*Colors.LINK_BLUE)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*Colors.BODY_TEXT)

        if url:
            pdf.write(line_h, clean_text, link=url)
        else:
            pdf.write(line_h, clean_text)

    # Reset
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*Colors.BODY_TEXT)


def _parse_inline_spans(text: str) -> list[tuple[str, str, Optional[str]]]:
    """Parse inline markdown into spans of (style, text, url).

    Handles: **bold**, *italic*, ***bold_italic***, [text](url)
    """
    spans = []
    # Pattern for bold_italic, bold, italic, links, plain text
    pattern = re.compile(
        r"\*\*\*(.+?)\*\*\*"        # ***bold italic***
        r"|\*\*(.+?)\*\*"           # **bold**
        r"|\*(.+?)\*"               # *italic*
        r"|\[([^\]]+)\]\(([^)]+)\)" # [text](url)
        r"|([^*\[]+)"              # plain text
    )

    for m in pattern.finditer(text):
        if m.group(1):
            spans.append(("bold_italic", m.group(1), None))
        elif m.group(2):
            spans.append(("bold", m.group(2), None))
        elif m.group(3):
            spans.append(("italic", m.group(3), None))
        elif m.group(4):
            spans.append(("link", m.group(4), m.group(5)))
        elif m.group(6):
            spans.append(("normal", m.group(6), None))

    return spans


# ═══════════════════════════════════════════════════════════
# Block Renderers
# ═══════════════════════════════════════════════════════════

_section_counter = 0


def _render_heading(pdf: FPDF, text: str, level: int) -> None:
    """Render a heading with colored accent card for level 2."""
    global _section_counter

    if level == 1:
        # Large title heading
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(*Colors.HEADING_DARK)
        pdf.multi_cell(0, 10, _clean(text))
        pdf.ln(4)
        return

    if level == 2:
        _section_counter += 1
        accent = Colors.ACCENTS[(_section_counter - 1) % len(Colors.ACCENTS)]

        # Ensure enough space for the card
        if pdf.get_y() > 250:
            pdf.add_page()

        y = pdf.get_y()
        card_y = y + 2

        # Card background
        pdf.set_fill_color(*Colors.CARD_BG)
        _draw_rounded_rect(pdf, 10, card_y, 190, 16, 3, "F")

        # Left accent bar
        pdf.set_fill_color(*accent)
        pdf.rect(10, card_y, 3, 16, "F")

        # Section number badge
        badge_cx = 20
        badge_cy = card_y + 8
        pdf.set_fill_color(*accent)
        _draw_circle(pdf, badge_cx, badge_cy, 5, "F")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*Colors.TITLE_WHITE)
        pdf.set_xy(badge_cx - 4, badge_cy - 3.5)
        pdf.cell(8, 7, str(_section_counter), align="C")

        # Heading text
        pdf.set_xy(28, card_y + 2)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*Colors.HEADING_DARK)
        pdf.cell(0, 12, _clean(text))

        pdf.set_y(card_y + 20)
        return

    # Levels 3-6
    sizes = {3: 12, 4: 11, 5: 10, 6: 10}
    size = sizes.get(level, 10)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", size)
    pdf.set_text_color(*Colors.HEADING_DARK)
    pdf.multi_cell(0, size * 0.55, _clean(text))
    pdf.ln(2)


def _render_bullet(pdf: FPDF, text: str, accent: tuple) -> None:
    """Render a bullet point with a colored circle marker."""
    x_start = pdf.get_x()
    y = pdf.get_y()

    # Colored bullet circle
    pdf.set_fill_color(*accent)
    _draw_circle(pdf, x_start + 14, y + 2.5, 1.5, "F")

    # Text starts at x_start + 19. Set left margin to align wrapped text.
    old_margin = pdf.l_margin
    indent_x = x_start + 19
    pdf.set_left_margin(indent_x)
    pdf.set_xy(indent_x, y)
    
    _render_rich_text(pdf, text, line_h=5)
    pdf.ln(6)
    
    # Restore margin and cursor
    pdf.set_left_margin(old_margin)
    pdf.set_x(old_margin)


def _render_sub_bullet(pdf: FPDF, text: str, accent: tuple) -> None:
    """Render a sub-bullet with a hollow circle marker."""
    x_start = pdf.get_x()
    y = pdf.get_y()

    # Hollow circle
    pdf.set_draw_color(*accent)
    pdf.set_line_width(0.4)
    _draw_circle(pdf, x_start + 22, y + 2.5, 1.2, "D")

    # Text starts at x_start + 27. Set left margin to align wrapped text.
    old_margin = pdf.l_margin
    indent_x = x_start + 27
    pdf.set_left_margin(indent_x)
    pdf.set_xy(indent_x, y)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*Colors.BODY_LIGHT)
    _render_rich_text(pdf, text, line_h=4.5)
    pdf.ln(5)
    
    # Restore margin and cursor
    pdf.set_left_margin(old_margin)
    pdf.set_x(old_margin)


def _render_numbered(pdf: FPDF, num: str, text: str, accent: tuple) -> None:
    """Render a numbered list item with a colored badge."""
    x_start = pdf.get_x()
    y = pdf.get_y()

    # Number badge
    pdf.set_fill_color(*accent)
    _draw_circle(pdf, x_start + 14, y + 2.5, 3.5, "F")
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*Colors.TITLE_WHITE)
    pdf.set_xy(x_start + 10.5, y)
    pdf.cell(7, 5, _clean(num), align="C")

    # Text starts at x_start + 21. Set left margin to align wrapped text.
    old_margin = pdf.l_margin
    indent_x = x_start + 21
    pdf.set_left_margin(indent_x)
    pdf.set_xy(indent_x, y)
    
    _render_rich_text(pdf, text, line_h=5)
    pdf.ln(6)
    
    # Restore margin and cursor
    pdf.set_left_margin(old_margin)
    pdf.set_x(old_margin)


def _render_paragraph(pdf: FPDF, text: str) -> None:
    """Render a paragraph with inline formatting support."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*Colors.BODY_TEXT)
    pdf.set_x(pdf.l_margin)
    _render_rich_text(pdf, text, line_h=5)
    pdf.ln(7)


def _render_blockquote(pdf: FPDF, text: str) -> None:
    """Render a blockquote with gray background and accent bar."""
    clean_text = _clean(text)

    # Calculate height using dry run
    pdf.set_font("Helvetica", "I", 10)
    lines = pdf.multi_cell(
        w=170, h=5, text=clean_text,
        dry_run=True, output="LINES",
    )
    block_h = max(len(lines) * 5 + 8, 16)

    if pdf.get_y() + block_h > 270:
        pdf.add_page()

    y = pdf.get_y()

    # Background
    pdf.set_fill_color(*Colors.BLOCKQUOTE_BG)
    _draw_rounded_rect(pdf, 14, y, 182, block_h, 3, "F")

    # Left accent bar
    accent = Colors.ACCENTS[_section_counter % len(Colors.ACCENTS)]
    pdf.set_fill_color(*accent)
    pdf.rect(14, y, 3, block_h, "F")

    # Quote text starts at X=21. Set left margin to align wrapped text.
    old_margin = pdf.l_margin
    pdf.set_left_margin(21)
    pdf.set_xy(21, y + 4)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(*Colors.BODY_LIGHT)
    
    # Render with inline formatting inside blockquote
    _render_rich_text(pdf, text, line_h=5)
    
    # Restore margin and cursor
    pdf.set_left_margin(old_margin)
    pdf.set_x(old_margin)
    pdf.set_y(y + block_h + 4)


def _render_code_block(pdf: FPDF, text: str) -> None:
    """Render a fenced code block with dark background."""
    clean_text = _clean(text)

    pdf.set_font("Courier", "", 8)
    lines = clean_text.split("\n")
    block_h = max(len(lines) * 4.5 + 10, 14)

    if pdf.get_y() + block_h > 270:
        pdf.add_page()

    y = pdf.get_y()

    # Dark background
    pdf.set_fill_color(*Colors.CODE_BG)
    _draw_rounded_rect(pdf, 14, y, 182, block_h, 3, "F")

    # Code text
    pdf.set_xy(18, y + 5)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(*Colors.CODE_TEXT)

    for line in lines:
        pdf.set_x(18)
        pdf.cell(0, 4.5, _clean(line))
        pdf.ln(4.5)

    pdf.set_y(y + block_h + 4)

    # Reset text color
    pdf.set_text_color(*Colors.BODY_TEXT)


def _render_table(pdf: FPDF, table_lines: list[str]) -> None:
    """Render a markdown pipe-table with styled headers and zebra striping using native FPDF.table."""
    if len(table_lines) < 2:
        return

    # Parse cells
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Skip separator rows (e.g., |---|---|)
        if cells and all(re.match(r"^[-:]+$", c) for c in cells):
            continue
        if cells:
            rows.append(cells)

    if not rows:
        return

    header = rows[0]
    data_rows = rows[1:]
    num_cols = len(header)

    if num_cols == 0:
        return

    from fpdf.fonts import FontFace

    # Define FontFace styles for header and alternate data rows
    header_style = FontFace(emphasis="B", color=Colors.TABLE_HEADER_TEXT, fill_color=Colors.TABLE_HEADER_BG)
    zebra_style = FontFace(fill_color=Colors.TABLE_ZEBRA_LIGHT)
    white_style = FontFace(fill_color=Colors.TABLE_ZEBRA_WHITE)

    # Render table using native fpdf2 table context manager.
    # It auto-wraps text and handles multiple pages beautifully.
    with pdf.table(align="CENTER", width=186) as table:
        # Header Row
        row = table.row()
        for cell in header:
            row.cell(_clean(cell), style=header_style, align="C")

        # Data Rows
        for idx, data_row in enumerate(data_rows):
            row_style = zebra_style if idx % 2 == 0 else white_style
            row = table.row()
            
            # Handle row matching column length to avoid index error
            for cell in data_row[:num_cols]:
                row.cell(_clean(cell), style=row_style, align="C")
            
            # Fill missing cells if any
            for _ in range(num_cols - len(data_row)):
                row.cell("", style=row_style, align="C")

    pdf.ln(4)


def _render_hr(pdf: FPDF) -> None:
    """Render a horizontal rule."""
    pdf.set_draw_color(*Colors.DIVIDER)
    pdf.set_line_width(0.4)
    y = pdf.get_y() + 2
    pdf.line(30, y, 180, y)
    pdf.ln(6)


# ═══════════════════════════════════════════════════════════
# Sources Appendix
# ═══════════════════════════════════════════════════════════

def _render_sources_appendix(pdf: FPDF, sources: list[dict]) -> None:
    """Render a styled sources/references appendix page."""
    if not sources:
        return

    pdf.add_page()

    # Section heading
    accent = Colors.ACCENTS[0]
    pdf.set_fill_color(*Colors.CARD_BG)
    _draw_rounded_rect(pdf, 10, pdf.get_y(), 190, 16, 3, "F")
    pdf.set_fill_color(*accent)
    pdf.rect(10, pdf.get_y(), 3, 16, "F")

    pdf.set_xy(16, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*Colors.HEADING_DARK)
    pdf.cell(0, 12, "References & Sources")
    pdf.ln(22)

    for idx, source in enumerate(sources, 1):
        title = source.get("title", f"Source {idx}")
        url = source.get("url", "")
        snippet = source.get("snippet", "")
        src_type = source.get("source", "web")

        # Alternating background
        if idx % 2 == 1:
            y = pdf.get_y()
            pdf.set_fill_color(*Colors.TABLE_ZEBRA_LIGHT)
            pdf.rect(12, y, 186, 20, "F")

        # Check page space
        if pdf.get_y() > 260:
            pdf.add_page()

        y = pdf.get_y()

        # Number badge
        badge_accent = Colors.ACCENTS[(idx - 1) % len(Colors.ACCENTS)]
        pdf.set_fill_color(*badge_accent)
        _draw_circle(pdf, 18, y + 4, 4, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*Colors.TITLE_WHITE)
        pdf.set_xy(14, y + 1)
        pdf.cell(8, 6, str(idx), align="C")

        # Title
        pdf.set_xy(26, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*Colors.BODY_TEXT)
        pdf.cell(0, 5, _clean(title[:80]))

        # URL
        pdf.set_xy(26, y + 5)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*Colors.LINK_BLUE)
        display_url = url[:90] + "..." if len(url) > 90 else url
        if url:
            pdf.cell(0, 4, _clean(display_url), link=url)
        pdf.ln()

        # Snippet
        if snippet:
            old_margin = pdf.l_margin
            pdf.set_left_margin(26)
            pdf.set_xy(26, y + 10)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*Colors.BODY_LIGHT)
            pdf.multi_cell(165, 3.5, _clean(snippet[:200]))
            pdf.set_left_margin(old_margin)
            pdf.set_x(old_margin)

        pdf.set_y(max(pdf.get_y(), y + 20) + 2)


# ═══════════════════════════════════════════════════════════
# Main Rendering Pipeline
# ═══════════════════════════════════════════════════════════

def _render_report_body(pdf: FPDF, markdown_text: str) -> None:
    """Parse markdown and render all blocks with infographic styling."""
    global _section_counter
    _section_counter = 0

    blocks = _parse_markdown_blocks(markdown_text)

    for block in blocks:
        btype = block["type"]
        accent = Colors.ACCENTS[_section_counter % len(Colors.ACCENTS)]

        if btype == "heading":
            _render_heading(pdf, block["content"], block["level"])
        elif btype == "bullet":
            _render_bullet(pdf, block["content"], accent)
        elif btype == "sub_bullet":
            _render_sub_bullet(pdf, block["content"], accent)
        elif btype == "numbered":
            _render_numbered(pdf, block["num"], block["content"], accent)
        elif btype == "paragraph":
            _render_paragraph(pdf, block["content"])
        elif btype == "table":
            _render_table(pdf, block["content"])
        elif btype == "blockquote":
            _render_blockquote(pdf, block["content"])
        elif btype == "code_block":
            _render_code_block(pdf, block["content"])
        elif btype == "hr":
            _render_hr(pdf)


# ═══════════════════════════════════════════════════════════
# Public API (unchanged signatures)
# ═══════════════════════════════════════════════════════════

def export_pdf(
    session_data: dict,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Export a research session's report as a premium styled PDF.

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
        pdf = _build_pdf(session_data)
        pdf.output(str(filepath))
        logger.info(f"PDF report exported to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise


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
    pdf = _build_pdf(session_data)
    return bytes(pdf.output())


def _build_pdf(session_data: dict) -> ResearchReportPDF:
    """Build the complete PDF document from session data."""
    query = session_data.get("user_query", "Research")
    report = session_data.get("final_report", "No report available.")
    created_at = session_data.get(
        "created_at", datetime.now(timezone.utc).isoformat()
    )
    sources = session_data.get("sources", [])

    pdf = ResearchReportPDF(title=_clean(query))
    pdf.report_date = f"Generated: {created_at}"
    pdf.alias_nb_pages()

    # ── Cover Page ──
    pdf.add_page()
    _render_cover_page(pdf, session_data)

    # ── Report Body ──
    pdf.add_page()
    _render_report_body(pdf, report)

    # ── Sources Appendix ──
    _render_sources_appendix(pdf, sources)

    return pdf
