"""
LangGraph Workflow — Research Agent Pipeline.

Assembles the complete research workflow:
  START → planner → researcher → analyst → summarizer → reporter → memory_saver → END

Each node is an async function that receives the full state
and returns a partial state update.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

from backend.schemas.state import ResearchState
from backend.agents.planner import planner_node
from backend.agents.researcher import researcher_node
from backend.agents.analyst import analyst_node
from backend.agents.summarizer import summarizer_node
from backend.agents.reporter import reporter_node

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Memory Saver Node (inline — lightweight)
# ──────────────────────────────────────────────

async def memory_saver_node(state: dict) -> dict:
    """
    Memory node: persists the research session to JSON storage.

    This is the final node before END. It saves the complete
    session to disk via the MemoryManager.
    """
    from backend.memory.memory_manager import MemoryManager

    timestamp = datetime.now(timezone.utc).isoformat()
    session_id = state.get("session_id", str(uuid.uuid4()))

    try:
        manager = MemoryManager()
        session_data = {
            "session_id": session_id,
            "user_query": state.get("user_query", ""),
            "research_plan": state.get("research_plan", {}),
            "sources": state.get("sources", []),
            "insights": state.get("insights", []),
            "summary": state.get("summary", ""),
            "final_report": state.get("final_report", ""),
            "logs": state.get("logs", []),
            "model": state.get("model", ""),
            "created_at": timestamp,
        }

        manager.save_session(session_id, session_data)

        logger.info(f"[Memory] Session {session_id} saved successfully")

        return {
            "memory": {
                "session_id": session_id,
                "saved_at": timestamp,
                "status": "saved",
            },
            "logs": [
                f"[{timestamp}] 💾 Memory: Session {session_id[:8]}... saved"
            ],
        }

    except Exception as e:
        logger.error(f"[Memory] Failed to save session: {e}")
        return {
            "memory": {
                "session_id": session_id,
                "saved_at": timestamp,
                "status": f"error: {e}",
            },
            "logs": [
                f"[{timestamp}] ❌ Memory: Failed to save session: {e}"
            ],
        }


# ──────────────────────────────────────────────
# Graph Construction
# ──────────────────────────────────────────────

def build_research_graph() -> StateGraph:
    """
    Build and compile the LangGraph research workflow.

    Graph topology:
        START → planner → researcher → analyst → summarizer
              → reporter → memory_saver → END

    Returns
    -------
    CompiledGraph
        A compiled LangGraph that can be invoked with initial state.
    """
    # Create the graph with our typed state
    builder = StateGraph(ResearchState)

    # Add all nodes
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("memory_saver", memory_saver_node)

    # Define the linear workflow edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "analyst")
    builder.add_edge("analyst", "summarizer")
    builder.add_edge("summarizer", "reporter")
    builder.add_edge("reporter", "memory_saver")
    builder.add_edge("memory_saver", END)

    # Compile
    graph = builder.compile()

    logger.info("Research workflow graph compiled successfully")
    return graph


# Lazy singleton — graph is built on first use, not at import time
_research_graph = None


def _get_graph():
    """Get or build the research graph (lazy singleton)."""
    global _research_graph
    if _research_graph is None:
        _research_graph = build_research_graph()
    return _research_graph


async def run_research(
    query: str,
    model: str | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Execute the full research pipeline.

    Parameters
    ----------
    query : str
        The research topic.
    model : str, optional
        OpenRouter model ID override.
    session_id : str, optional
        Session ID (generated if not provided).

    Returns
    -------
    dict
        The final state after all nodes have executed.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    initial_state: ResearchState = {
        "user_query": query,
        "session_id": session_id,
        "model": model or "",
        "logs": [
            f"[{datetime.now(timezone.utc).isoformat()}] 🚀 Starting research: "
            f"'{query}' (session: {session_id[:8]}...)"
        ],
    }

    logger.info(f"Starting research pipeline for: '{query}'")

    graph = _get_graph()
    result = await graph.ainvoke(initial_state)

    logger.info(
        f"Research pipeline completed for: '{query}' "
        f"(session: {session_id[:8]}...)"
    )

    return dict(result)
