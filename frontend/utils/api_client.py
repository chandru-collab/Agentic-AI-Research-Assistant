"""
API Client for communicating with the FastAPI backend.
If backend is unreachable, falls back to direct in-process execution.
"""

from __future__ import annotations

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    """HTTP client for the FastAPI backend with in-process fallback."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._backend_available = None

    def health_check(self) -> dict:
        """Check backend health."""
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(self._url("/health"))
                resp.raise_for_status()
                self._backend_available = True
                return resp.json()
        except Exception:
            self._backend_available = False
            return {"status": "in-process", "message": "Using local in-process fallback"}

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def is_backend_running(self) -> bool:
        if self._backend_available is None:
            self.health_check()
        return self._backend_available

    def run_research(
        self,
        query: str,
        model: Optional[str] = None,
        timeout: float = 300.0,
    ) -> dict:
        if self.is_backend_running():
            payload = {"query": query}
            if model:
                payload["model"] = model

            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(self._url("/research"), json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except httpx.TimeoutException:
                logger.error("Research request timed out")
                return {"error": "Request timed out. The research may still be processing."}
            except httpx.HTTPStatusError as e:
                logger.error(f"Research failed: {e.response.text}")
                return {"error": e.response.json().get("detail", str(e))}
            except Exception as e:
                logger.error(f"Research request failed: {e}")
                # Fallback to local
                pass

        # In-process execution fallback
        try:
            import asyncio
            import concurrent.futures
            from backend.graph.workflow import run_research as backend_run_research

            # Run in a ThreadPoolExecutor to prevent blocking Streamlit's event loop
            # and to safely execute async functions synchronously.
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, backend_run_research(query=query, model=model))
                result = future.result()
            return result
        except Exception as e:
            logger.error(f"In-process research failed: {e}")
            return {"error": f"Local run failed: {str(e)}"}

    def get_history(self) -> list[dict]:
        if self.is_backend_running():
            try:
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get(self._url("/history"))
                    resp.raise_for_status()
                    return resp.json()
            except Exception:
                pass

        try:
            from backend.memory.memory_manager import MemoryManager
            manager = MemoryManager()
            return manager.list_sessions()
        except Exception as e:
            logger.error(f"In-process history fetch failed: {e}")
            return []

    def get_report(self, session_id: str) -> dict:
        if self.is_backend_running():
            try:
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get(self._url(f"/report/{session_id}"))
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return {"error": "Session not found"}
                pass
            except Exception:
                pass

        try:
            from backend.memory.memory_manager import MemoryManager
            manager = MemoryManager()
            session = manager.load_session(session_id)
            if not session:
                return {"error": "Session not found"}
            return session
        except Exception as e:
            logger.error(f"In-process report fetch failed: {e}")
            return {"error": str(e)}

    def export_pdf(self, session_id: str) -> bytes | None:
        if self.is_backend_running():
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        self._url("/export/pdf"),
                        json={"session_id": session_id},
                    )
                    resp.raise_for_status()
                    return resp.content
            except Exception:
                pass

        try:
            from backend.memory.memory_manager import MemoryManager
            from backend.export.pdf_export import get_pdf_bytes
            manager = MemoryManager()
            session = manager.load_session(session_id)
            if not session:
                return None
            return get_pdf_bytes(session)
        except Exception as e:
            logger.error(f"In-process PDF export failed: {e}")
            return None

    def export_markdown(self, session_id: str) -> str | None:
        if self.is_backend_running():
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        self._url("/export/markdown"),
                        json={"session_id": session_id},
                    )
                    resp.raise_for_status()
                    return resp.text
            except Exception:
                pass

        try:
            from backend.memory.memory_manager import MemoryManager
            from backend.export.markdown_export import get_markdown_content
            manager = MemoryManager()
            session = manager.load_session(session_id)
            if not session:
                return None
            return get_markdown_content(session)
        except Exception as e:
            logger.error(f"In-process Markdown export failed: {e}")
            return None
