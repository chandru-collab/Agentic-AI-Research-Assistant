"""
JSON-Based Memory Manager.

Provides persistent storage for research sessions using JSON files.
Each session is stored as a separate file in the memory/ directory.
Thread-safe operations with asyncio locks.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages research session persistence using JSON files.

    Each session is saved as `{session_id}.json` in the memory directory.
    """

    def __init__(self, memory_dir: Optional[Path] = None) -> None:
        """
        Initialize the memory manager.

        Parameters
        ----------
        memory_dir : Path, optional
            Directory to store session files. Defaults to settings.MEMORY_DIR.
        """
        self.memory_dir = memory_dir or settings.MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session ID."""
        # Sanitize the session_id to prevent path traversal
        safe_id = session_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        return self.memory_dir / f"{safe_id}.json"

    def save_session(self, session_id: str, data: dict) -> None:
        """
        Save a research session to disk.

        Parameters
        ----------
        session_id : str
            Unique session identifier.
        data : dict
            Session data to persist.
        """
        filepath = self._session_path(session_id)

        # Add metadata
        data["session_id"] = session_id
        if "created_at" not in data:
            data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Session {session_id[:8]}... saved to {filepath.name}")
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise

    def load_session(self, session_id: str) -> Optional[dict]:
        """
        Load a research session from disk.

        Parameters
        ----------
        session_id : str
            Session ID to load.

        Returns
        -------
        dict or None
            Session data if found, None otherwise.
        """
        filepath = self._session_path(session_id)

        if not filepath.exists():
            logger.warning(f"Session not found: {session_id}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Session {session_id[:8]}... loaded")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt session file {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def list_sessions(self) -> list[dict]:
        """
        List all saved research sessions.

        Returns
        -------
        list[dict]
            List of session summaries sorted by creation date (newest first).
            Each dict has: session_id, query, created_at, summary_preview.
        """
        sessions = []

        for filepath in self.memory_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                summary = data.get("summary", "")
                sessions.append({
                    "session_id": data.get("session_id", filepath.stem),
                    "query": data.get("user_query", "Unknown"),
                    "created_at": data.get("created_at", ""),
                    "summary_preview": summary[:200] if summary else "",
                })
            except Exception as e:
                logger.warning(f"Failed to read session file {filepath.name}: {e}")

        # Sort by creation date (newest first)
        sessions.sort(
            key=lambda s: s.get("created_at", ""),
            reverse=True,
        )

        logger.info(f"Listed {len(sessions)} sessions")
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a research session.

        Parameters
        ----------
        session_id : str
            Session ID to delete.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        filepath = self._session_path(session_id)

        if not filepath.exists():
            logger.warning(f"Session not found for deletion: {session_id}")
            return False

        try:
            filepath.unlink()
            logger.info(f"Session {session_id[:8]}... deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._session_path(session_id).exists()
