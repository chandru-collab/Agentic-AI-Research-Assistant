"""
FastAPI API Routes.

All REST endpoints for the research assistant:
  POST /research        — Execute research workflow
  GET  /history         — List past sessions
  GET  /report/{id}     — Get a specific report
  POST /export/pdf      — Export report as PDF
  POST /export/markdown — Export report as Markdown
  GET  /health          — Health check
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.config import settings
from backend.schemas.models import (
    ResearchRequest,
    ResearchResponse,
    ExportRequest,
    HealthResponse,
    HistoryItem,
)
from backend.memory.memory_manager import MemoryManager
from backend.export.pdf_export import get_pdf_bytes, export_pdf
from backend.export.markdown_export import get_markdown_content, export_markdown

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────
# GET /
# ──────────────────────────────────────────────

@router.get("/")
async def root_endpoint():
    """Welcome root endpoint."""
    return {
        "message": "Welcome to the Agentic AI Research Assistant API",
        "health": "/health",
        "docs": "/docs"
    }


# ──────────────────────────────────────────────
# POST /research
# ──────────────────────────────────────────────

@router.post("/research", response_model=ResearchResponse)
async def run_research_endpoint(request: ResearchRequest):
    """
    Execute the full research workflow for a given topic.

    Runs the LangGraph pipeline:
    Planner → Researcher → Analyst → Summarizer → Reporter → Memory
    """
    logger.info(f"Research request received: '{request.query}'")

    try:
        # Import here to avoid circular imports at module level
        from backend.graph.workflow import run_research

        result = await run_research(
            query=request.query,
            model=request.model,
        )

        return ResearchResponse(
            session_id=result.get("session_id", "unknown"),
            query=result.get("user_query", request.query),
            research_plan=result.get("research_plan", {}),
            sources=result.get("sources", []),
            insights=result.get("insights", []),
            summary=result.get("summary", ""),
            final_report=result.get("final_report", ""),
            logs=result.get("logs", []),
            created_at=result.get("memory", {}).get(
                "saved_at", datetime.now(timezone.utc).isoformat()
            ),
        )

    except Exception as e:
        logger.error(f"Research pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline failed: {str(e)}",
        )


# ──────────────────────────────────────────────
# GET /history
# ──────────────────────────────────────────────

@router.get("/history", response_model=list[HistoryItem])
async def get_history():
    """List all past research sessions."""
    try:
        manager = MemoryManager()
        sessions = manager.list_sessions()
        return [HistoryItem(**s) for s in sessions]
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# GET /report/{id}
# ──────────────────────────────────────────────

@router.get("/report/{session_id}")
async def get_report(session_id: str):
    """Retrieve a specific research report by session ID."""
    manager = MemoryManager()
    session = manager.load_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ResearchResponse(
        session_id=session.get("session_id", session_id),
        query=session.get("user_query", ""),
        research_plan=session.get("research_plan", {}),
        sources=session.get("sources", []),
        insights=session.get("insights", []),
        summary=session.get("summary", ""),
        final_report=session.get("final_report", ""),
        logs=session.get("logs", []),
        created_at=session.get("created_at", ""),
    )


# ──────────────────────────────────────────────
# POST /export/pdf
# ──────────────────────────────────────────────

@router.post("/export/pdf")
async def export_pdf_endpoint(request: ExportRequest):
    """Export a research report as a PDF file."""
    manager = MemoryManager()
    session = manager.load_session(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        pdf_bytes = get_pdf_bytes(session)
        query = session.get("user_query", "research")
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-") else "_"
            for c in query[:40]
        ).strip()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'
            },
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF export failed: {str(e)}",
        )


# ──────────────────────────────────────────────
# POST /export/markdown
# ──────────────────────────────────────────────

@router.post("/export/markdown")
async def export_markdown_endpoint(request: ExportRequest):
    """Export a research report as a Markdown file."""
    manager = MemoryManager()
    session = manager.load_session(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        md_content = get_markdown_content(session)
        query = session.get("user_query", "research")
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-") else "_"
            for c in query[:40]
        ).strip()

        return Response(
            content=md_content.encode("utf-8"),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_report.md"'
            },
        )
    except Exception as e:
        logger.error(f"Markdown export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Markdown export failed: {str(e)}",
        )


# ──────────────────────────────────────────────
# GET /health
# ──────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
