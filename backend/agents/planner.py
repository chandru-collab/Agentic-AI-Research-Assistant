"""
Planner Agent Node.

Understands the user's research intent and creates a structured
research plan with objectives, sub-topics, and search queries.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from backend.services.llm_service import invoke_llm_json

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an expert research planner who creates highly effective research strategies.
Your plans consistently lead to comprehensive, accurate research outcomes.

Given a research topic, produce a JSON object with exactly these keys:
{
    "objectives": ["list of 3-5 clear, specific, measurable research objectives"],
    "sub_topics": ["list of 4-6 specific sub-topics covering different angles"],
    "search_queries": ["list of 8-12 optimized search queries"]
}

GUIDELINES FOR OBJECTIVES:
- Each objective should answer a specific question (what, why, how, who, when)
- Include at least one objective about current state/facts
- Include at least one objective about challenges or limitations
- Include at least one objective about future direction or trends

GUIDELINES FOR SUB-TOPICS:
- Cover fundamentals/definitions, applications, key players, challenges, and trends
- Each sub-topic should be distinct — no overlapping coverage
- Include both technical and practical/business perspectives

GUIDELINES FOR SEARCH QUERIES:
- Make queries specific and keyword-rich (NOT vague questions)
- Include a mix of:
  * Definitional queries: "what is [topic] definition explained"
  * Current state: "[topic] 2024 2025 current state statistics"
  * Key players: "[topic] leading companies organizations"
  * Applications: "[topic] real-world applications use cases"
  * Challenges: "[topic] challenges problems limitations"
  * Trends: "[topic] future trends predictions outlook"
  * Comparisons: "[topic] vs [alternative] comparison"
  * Expert views: "[topic] expert analysis review"
- Avoid overly broad single-word queries
- Each query should be 3-8 words for optimal search results
"""


async def planner_node(state: dict) -> dict:
    """
    Planner node for the LangGraph workflow.

    Takes the user_query from state, invokes the LLM to create
    a structured research plan.

    Parameters
    ----------
    state : dict
        Current workflow state with 'user_query'.

    Returns
    -------
    dict
        Partial state update with 'research_plan' and 'logs'.
    """
    user_query = state.get("user_query", "")
    model = state.get("model")
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"[Planner] Starting planning for: '{user_query}'")

    prompt = f"""Create a detailed research plan for the following topic:

TOPIC: {user_query}

Produce a structured JSON research plan."""

    try:
        response = await invoke_llm_json(
            prompt=prompt,
            model=model,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.2,
        )

        # Parse the JSON response
        # Clean up potential markdown code fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove code fence markers
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )

        research_plan = json.loads(cleaned)

        # Validate required keys
        for key in ("objectives", "sub_topics", "search_queries"):
            if key not in research_plan:
                research_plan[key] = []

        logger.info(
            f"[Planner] Plan created: "
            f"{len(research_plan.get('objectives', []))} objectives, "
            f"{len(research_plan.get('sub_topics', []))} sub-topics, "
            f"{len(research_plan.get('search_queries', []))} queries"
        )

        return {
            "research_plan": research_plan,
            "logs": [
                f"[{timestamp}] 📋 Planner: Created research plan with "
                f"{len(research_plan.get('objectives', []))} objectives, "
                f"{len(research_plan.get('sub_topics', []))} sub-topics, "
                f"{len(research_plan.get('search_queries', []))} search queries"
            ],
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Planner] Failed to parse LLM response as JSON: {e}")
        # Create a fallback plan
        fallback_plan = {
            "objectives": [f"Research and understand {user_query}"],
            "sub_topics": [user_query],
            "search_queries": [
                user_query,
                f"{user_query} overview",
                f"{user_query} recent developments",
                f"{user_query} applications",
                f"{user_query} challenges",
            ],
        }
        return {
            "research_plan": fallback_plan,
            "logs": [
                f"[{timestamp}] ⚠️ Planner: LLM response was not valid JSON. "
                f"Using fallback plan with basic queries."
            ],
        }

    except Exception as e:
        logger.error(f"[Planner] Unexpected error: {e}")
        fallback_plan = {
            "objectives": [f"Research {user_query}"],
            "sub_topics": [user_query],
            "search_queries": [user_query, f"what is {user_query}"],
        }
        return {
            "research_plan": fallback_plan,
            "logs": [
                f"[{timestamp}] ❌ Planner: Error occurred ({e}). "
                f"Using minimal fallback plan."
            ],
        }
