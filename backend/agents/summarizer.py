"""
Summarizer Agent Node.

Generates concise structured notes and an executive summary
from the analyzed insights.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.services.llm_service import invoke_llm

logger = logging.getLogger(__name__)

SUMMARIZER_SYSTEM_PROMPT = """You are an expert research summarizer who distills complex research findings
into clear, accurate, and well-structured executive summaries.

CRITICAL ACCURACY RULES:
- ONLY summarize facts and findings present in the provided insights
- NEVER add information, statistics, or claims not found in the input
- Use precise language — avoid vague qualifiers like "many", "several" without context
- If insights are limited, produce a shorter but accurate summary rather than padding with filler

Create a summary that includes:
1. **Overview**: A concise opening paragraph (2-3 sentences) stating the core finding
2. **Key Findings**: 5-8 bullet points, each stating one specific, factual finding
3. **Notable Trends**: 2-4 patterns or trends observed across the research
4. **Implications**: What these findings mean in practical terms

Guidelines:
- Be concise but comprehensive — every sentence must add value
- Use clear, professional language accessible to a general audience
- Start each bullet point with a **bold key term** followed by a colon
- Highlight the most important and well-supported findings first
- Format using Markdown for readability (bold, italic, bullet points)
- Keep the total summary under 500 words
- Use direct, active voice — avoid passive constructions
"""


async def summarizer_node(state: dict) -> dict:
    """
    Summarizer node for the LangGraph workflow.

    Takes insights from state and generates an executive summary.

    Parameters
    ----------
    state : dict
        Current workflow state with 'insights', 'user_query'.

    Returns
    -------
    dict
        Partial state update with 'summary' and 'logs'.
    """
    insights = state.get("insights", [])
    user_query = state.get("user_query", "")
    model = state.get("model")
    timestamp = datetime.now(timezone.utc).isoformat()

    if not insights:
        logger.warning("[Summarizer] No insights to summarize")
        return {
            "summary": "No insights were available to generate a summary.",
            "logs": [
                f"[{timestamp}] ⚠️ Summarizer: No insights available"
            ],
        }

    # Format insights for the prompt
    insights_text = "\n".join(
        f"  {i + 1}. {insight}" for i, insight in enumerate(insights)
    )

    prompt = f"""Create an executive summary for the following research topic and insights.

RESEARCH TOPIC: {user_query}

ANALYZED INSIGHTS:
{insights_text}

Generate a well-structured executive summary in Markdown format."""

    try:
        summary = await invoke_llm(
            prompt=prompt,
            model=model,
            system_prompt=SUMMARIZER_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
        )

        if not summary or not summary.strip():
            summary = "Summary generation produced empty results."

        logger.info(
            f"[Summarizer] Generated summary ({len(summary)} chars) "
            f"from {len(insights)} insights"
        )

        return {
            "summary": summary.strip(),
            "logs": [
                f"[{timestamp}] 📝 Summarizer: Generated executive summary "
                f"({len(summary)} chars) from {len(insights)} insights"
            ],
        }

    except Exception as e:
        logger.error(f"[Summarizer] Error: {e}")
        # Create a basic fallback summary
        fallback = f"## Executive Summary: {user_query}\n\n"
        fallback += "### Key Findings\n\n"
        for insight in insights[:5]:
            fallback += f"- {insight}\n"
        fallback += (
            "\n*Note: This is a fallback summary generated due to an "
            "LLM processing error.*"
        )

        return {
            "summary": fallback,
            "logs": [
                f"[{timestamp}] ⚠️ Summarizer: Error ({e}), "
                f"generated fallback summary"
            ],
        }
