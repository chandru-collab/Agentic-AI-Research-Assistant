"""
FastAPI Backend Entry Point.

Configures the FastAPI application with CORS, logging,
lifespan events, and router includes.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    logger.info(f"   Default model: {settings.DEFAULT_MODEL}")
    logger.info(f"   Reranker model: {settings.RERANKER_MODEL}")
    logger.info(f"   Reports dir: {settings.REPORTS_DIR}")
    logger.info(f"   Memory dir: {settings.MEMORY_DIR}")

    # Validate settings on startup
    try:
        settings.validate()
        logger.info("   ✅ API key configured")
    except ValueError as e:
        logger.warning(f"   ⚠️ {e}")

    yield

    logger.info(f"🛑 {settings.APP_NAME} shutting down...")


# ──────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready Agentic AI Research Assistant powered by "
        "LangGraph and OpenRouter. Performs multi-step research with "
        "planning, searching, analysis, summarization, and report generation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from backend.api.routes import router  # noqa: E402

app.include_router(router)


# ──────────────────────────────────────────────
# Run directly
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
