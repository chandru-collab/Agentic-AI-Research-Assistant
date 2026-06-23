"""
Tests for Export modules.
"""

import pytest
from pathlib import Path

from backend.export.markdown_export import export_markdown, get_markdown_content
from backend.export.pdf_export import export_pdf, get_pdf_bytes


@pytest.fixture
def sample_session():
    """Sample session data for export tests."""
    return {
        "session_id": "test-export-123",
        "user_query": "Test Research Topic",
        "research_plan": {
            "objectives": ["Understand the topic"],
            "sub_topics": ["Sub-topic 1"],
            "search_queries": ["test query"],
        },
        "sources": [
            {
                "title": "Source 1",
                "url": "http://example.com/1",
                "snippet": "This is a snippet from source one with details.",
                "source": "duckduckgo",
            },
            {
                "title": "Source 2",
                "url": "http://example.com/2",
                "snippet": "Another snippet providing background context.",
                "source": "wikipedia",
            },
            {
                "title": "Source 3",
                "url": "http://example.com/3",
                "snippet": "Third source with additional research data.",
                "source": "duckduckgo",
            },
        ],
        "insights": ["Insight 1", "Insight 2", "Insight 3"],
        "summary": "This is a test summary of the research.",
        "final_report": (
            "# Test Research Topic\n\n"
            "## Introduction\n\n"
            "This is a **bold** statement and an *italic* note. "
            "See [Example](http://example.com) for details.\n\n"
            "> This is an important blockquote that highlights "
            "> a key finding from the research.\n\n"
            "## Key Findings\n\n"
            "1. Finding one with **emphasis**\n"
            "2. Finding two with *details*\n"
            "3. Finding three is also important\n\n"
            "## Data Overview\n\n"
            "| Metric | Value | Change |\n"
            "|--------|-------|--------|\n"
            "| Users  | 1.2M  | +15%   |\n"
            "| Revenue| $4.5B | +22%   |\n"
            "| Growth | 18%   | +3pp   |\n\n"
            "## Technical Details\n\n"
            "- First bullet point\n"
            "- Second bullet with **bold** text\n"
            "  - Sub-bullet indented\n"
            "  - Another sub-bullet\n"
            "- Third bullet point\n\n"
            "```\n"
            "def example():\n"
            "    return 'hello world'\n"
            "```\n\n"
            "---\n\n"
            "## Conclusion\n\n"
            "The research demonstrates significant progress "
            "across all measured dimensions.\n\n"
            "## References\n\n"
            "[1] Source 1 - http://example.com/1\n"
            "[2] Source 2 - http://example.com/2\n"
        ),
        "created_at": "2025-01-01T00:00:00Z",
    }


class TestMarkdownExport:
    """Tests for Markdown export."""

    def test_export_creates_file(self, sample_session, tmp_path):
        """Should create a .md file."""
        filepath = export_markdown(sample_session, output_dir=tmp_path)
        assert filepath.exists()
        assert filepath.suffix == ".md"

    def test_export_contains_report(self, sample_session, tmp_path):
        """Exported file should contain the report content."""
        filepath = export_markdown(sample_session, output_dir=tmp_path)
        content = filepath.read_text(encoding="utf-8")
        assert "Test Research Topic" in content
        assert "test-export-123" in content

    def test_get_markdown_content(self, sample_session):
        """Should return markdown string with metadata."""
        content = get_markdown_content(sample_session)
        assert "Test Research Topic" in content
        assert "test-export-123" in content
        assert "---" in content  # YAML frontmatter


class TestPDFExport:
    """Tests for PDF export."""

    def test_export_creates_file(self, sample_session, tmp_path):
        """Should create a .pdf file."""
        filepath = export_pdf(sample_session, output_dir=tmp_path)
        assert filepath.exists()
        assert filepath.suffix == ".pdf"
        assert filepath.stat().st_size > 0

    def test_get_pdf_bytes(self, sample_session):
        """Should return non-empty bytes."""
        pdf_bytes = get_pdf_bytes(sample_session)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"  # PDF magic number

    def test_pdf_substantial_size(self, sample_session):
        """Enhanced PDF with rich content should be substantial."""
        pdf_bytes = get_pdf_bytes(sample_session)
        # The infographic-style PDF should be larger than a minimal one
        assert len(pdf_bytes) > 2000
