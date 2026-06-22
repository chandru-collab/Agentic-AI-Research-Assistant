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
            {"title": "Source 1", "url": "http://example.com/1", "source": "duckduckgo"},
            {"title": "Source 2", "url": "http://example.com/2", "source": "wikipedia"},
        ],
        "insights": ["Insight 1", "Insight 2"],
        "summary": "This is a test summary of the research.",
        "final_report": (
            "# Test Research Topic\n\n"
            "## Introduction\n\n"
            "This is a test report.\n\n"
            "## Key Findings\n\n"
            "1. Finding one\n"
            "2. Finding two\n\n"
            "## References\n\n"
            "[1] Source 1 - http://example.com/1\n"
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
