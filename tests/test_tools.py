"""
Tests for search tools.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestSearchDuckDuckGo:
    """Tests for DuckDuckGo search."""

    @pytest.mark.asyncio
    async def test_search_returns_list(self):
        """Search should return a list of dicts."""
        from backend.tools.search_tools import search_duckduckgo

        with patch("backend.tools.search_tools.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.text.return_value = [
                {
                    "title": "Test Result",
                    "href": "https://example.com",
                    "body": "Test snippet",
                }
            ]
            mock_ddgs.return_value = mock_instance

            results = await search_duckduckgo("test query")
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_handles_error_gracefully(self):
        """Search should return empty list on error."""
        from backend.tools.search_tools import search_duckduckgo

        with patch("backend.tools.search_tools.DDGS", side_effect=Exception("API error")):
            results = await search_duckduckgo("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_result_format(self):
        """Each result should have title, url, snippet, source keys."""
        from backend.tools.search_tools import search_duckduckgo

        with patch("backend.tools.search_tools.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.text.return_value = [
                {
                    "title": "Title",
                    "href": "https://example.com",
                    "body": "Snippet",
                }
            ]
            mock_ddgs.return_value = mock_instance

            results = await search_duckduckgo("test")
            assert len(results) == 1
            result = results[0]
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert result["source"] == "duckduckgo"


class TestSearchWikipedia:
    """Tests for Wikipedia search."""

    @pytest.mark.asyncio
    async def test_search_handles_error_gracefully(self):
        """Search should return empty list on error."""
        from backend.tools.search_tools import search_wikipedia

        with patch("backend.tools.search_tools.wikipedia") as mock_wiki:
            mock_wiki.search.side_effect = Exception("Network error")
            results = await search_wikipedia("test query")
            assert results == []


class TestSearchAll:
    """Tests for combined search."""

    @pytest.mark.asyncio
    async def test_deduplication(self):
        """Combined search should deduplicate by URL."""
        from backend.tools.search_tools import search_all

        with patch("backend.tools.search_tools.search_duckduckgo") as mock_ddg, \
             patch("backend.tools.search_tools.search_wikipedia") as mock_wiki:
            mock_ddg.return_value = [
                {"title": "A", "url": "https://example.com/a", "snippet": "s", "source": "ddg"}
            ]
            mock_wiki.return_value = [
                {"title": "A dup", "url": "https://example.com/a", "snippet": "s2", "source": "wiki"},
                {"title": "B", "url": "https://example.com/b", "snippet": "s3", "source": "wiki"},
            ]

            results = await search_all("test")
            urls = [r["url"] for r in results]
            assert len(urls) == len(set(urls))  # No duplicates
