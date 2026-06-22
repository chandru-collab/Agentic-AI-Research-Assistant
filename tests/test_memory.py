"""
Tests for Memory Manager.
"""

import json
import pytest
import tempfile
from pathlib import Path

from backend.memory.memory_manager import MemoryManager


@pytest.fixture
def temp_memory_dir(tmp_path):
    """Create a temporary memory directory."""
    return tmp_path / "memory"


@pytest.fixture
def manager(temp_memory_dir):
    """Create a MemoryManager with a temp directory."""
    return MemoryManager(memory_dir=temp_memory_dir)


class TestMemoryManager:
    """Tests for MemoryManager."""

    def test_save_and_load_session(self, manager):
        """Should save and load a session correctly."""
        data = {
            "user_query": "Test research",
            "summary": "Test summary",
            "final_report": "Test report",
            "sources": [{"title": "Source 1", "url": "http://example.com"}],
        }

        manager.save_session("test-123", data)
        loaded = manager.load_session("test-123")

        assert loaded is not None
        assert loaded["user_query"] == "Test research"
        assert loaded["session_id"] == "test-123"
        assert "created_at" in loaded
        assert "updated_at" in loaded

    def test_load_nonexistent_session(self, manager):
        """Should return None for nonexistent sessions."""
        result = manager.load_session("nonexistent")
        assert result is None

    def test_list_sessions(self, manager):
        """Should list all saved sessions."""
        for i in range(3):
            manager.save_session(f"session-{i}", {
                "user_query": f"Query {i}",
                "summary": f"Summary {i}",
            })

        sessions = manager.list_sessions()
        assert len(sessions) == 3

    def test_list_sessions_sorted_by_date(self, manager):
        """Sessions should be sorted newest first."""
        manager.save_session("old", {
            "user_query": "Old",
            "created_at": "2024-01-01T00:00:00",
        })
        manager.save_session("new", {
            "user_query": "New",
            "created_at": "2025-01-01T00:00:00",
        })

        sessions = manager.list_sessions()
        assert sessions[0]["session_id"] == "new"

    def test_delete_session(self, manager):
        """Should delete a session."""
        manager.save_session("to-delete", {"user_query": "Delete me"})
        assert manager.session_exists("to-delete")

        result = manager.delete_session("to-delete")
        assert result is True
        assert not manager.session_exists("to-delete")

    def test_delete_nonexistent_session(self, manager):
        """Should return False for nonexistent sessions."""
        result = manager.delete_session("nonexistent")
        assert result is False

    def test_session_exists(self, manager):
        """Should correctly check session existence."""
        manager.save_session("exists", {"user_query": "Test"})
        assert manager.session_exists("exists")
        assert not manager.session_exists("nope")

    def test_path_traversal_protection(self, manager):
        """Should sanitize session IDs to prevent path traversal."""
        manager.save_session("../../etc/passwd", {"user_query": "Naughty"})
        # Should not create files outside the memory directory
        assert not Path("/etc/passwd.json").exists()
        # Should create a sanitized file inside the memory dir
        sessions = manager.list_sessions()
        assert len(sessions) == 1
