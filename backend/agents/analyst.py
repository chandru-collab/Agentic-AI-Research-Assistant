"""
Analyst Agent Node.

Extracts key information from search results, removes duplicates,
organizes findings into structured insights.
Optionally uses the NVIDIA vision reranker to score result relevance.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from backend.services.llm_service import invoke_llm_json
from backend.services.reranker_service import rerank_search_results

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = """You are an expert research analyst known for extracting accurate, specific,
and well-sourced insights from raw search results.

Given search results for a research topic, produce a JSON object with exactly this key:
{
    "insights": [
        "Insight 1: [Factual claim] — [Supporting evidence/data from the source]",
        "Insight 2: [Another distinct, verified finding]",
        ...
    ]
}

CRITICAL ACCURACY RULES:
- ONLY extract facts that are explicitly stated in the search results
- NEVER invent, assume, or extrapolate data not present in the sources
- Include specific numbers, dates, names, and metrics when available in the source
- If a source is vague, extract the insight as-is without adding made-up specifics
- Each insight must be traceable back to one or more search results

Guidelines:
- Extract 8-15 key insights from the search results
- Remove duplicate or near-duplicate information
- Each insight should follow this pattern:
  "[Key topic/term]: [Specific factual finding]. [Supporting detail or context from source]."
- Cover different aspects: definitions, current state, applications, challenges, trends, key players
- Prioritize concrete, data-backed information over vague generalities
- Include the source result number when referencing specific data (e.g., 'According to Result 3, ...')
- Rank insights by importance and reliability of the source
"""


async def analyst_node(state: dict) -> dict:
    """
    Analyst node for the LangGraph workflow.

    Takes search_results from state, optionally reranks them,
    then uses LLM to extract deduplicated key insights.

    Parameters
    ----------
    state : dict
        Current workflow state with 'search_results', 'user_query'.

    Returns
    -------
    dict
        Partial state update with 'insights', 'sources' (reranked), and 'logs'.
    """
    search_results = state.get("search_results", [])
    user_query = state.get("user_query", "")
    model = state.get("model")
    timestamp = datetime.now(timezone.utc).isoformat()

    if not search_results:
        logger.warning("[Analyst] No search results to analyze")
        return {
            "insights": ["No search results were available for analysis."],
            "logs": [
                f"[{timestamp}] ⚠️ Analyst: No search results to analyze"
            ],
        }

    # Step 1: Rerank search results using vision reranker
    logger.info(f"[Analyst] Reranking {len(search_results)} results...")
    try:
        reranked_results = await rerank_search_results(
            query=user_query,
            search_results=search_results,
            top_k=15,
        )
        rerank_log = (
            f"Reranked {len(search_results)} results → "
            f"top {len(reranked_results)}"
        )
    except Exception as e:
        logger.warning(f"[Analyst] Reranking failed, using original: {e}")
        reranked_results = search_results[:15]
        rerank_log = f"Reranking failed, using top {len(reranked_results)} as-is"

    # Step 2: Format results for LLM analysis
    formatted_results = ""
    for i, result in enumerate(reranked_results, 1):
        score = result.get("relevance_score", "N/A")
        formatted_results += (
            f"\n--- Result {i} (source: {result.get('source', 'unknown')}, "
            f"relevance: {score}) ---\n"
            f"Title: {result.get('title', 'Untitled')}\n"
            f"URL: {result.get('url', 'N/A')}\n"
            f"Content: {result.get('snippet', 'No content')}\n"
        )

    prompt = f"""Analyze the following search results for the research topic: "{user_query}"

SEARCH RESULTS:
{formatted_results}

Extract the most important, non-redundant insights from these results.
Return as JSON with an "insights" key containing a list of insight strings."""

    try:
        response = await invoke_llm_json(
            prompt=prompt,
            model=model,
            system_prompt=ANALYST_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=4096,
        )

        # Parse JSON
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )

        parsed = json.loads(cleaned)
        insights = parsed.get("insights", [])

        if not insights:
            insights = ["Analysis completed but no specific insights were extracted."]

        logger.info(f"[Analyst] Extracted {len(insights)} insights")

        # Update sources with reranked versions
        reranked_sources = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "relevance_score": r.get("relevance_score", 0.5),
            }
            for r in reranked_results
        ]

        return {
            "insights": insights,
            "sources": reranked_sources,
            "logs": [
                f"[{timestamp}] 🔬 Analyst: {rerank_log}. "
                f"Extracted {len(insights)} key insights"
            ],
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Analyst] JSON parse error: {e}")
        # Extract insights from raw text as fallback
        fallback_insights = [
            line.strip().lstrip("- •*")
            for line in response.split("\n")
            if line.strip() and len(line.strip()) > 20
        ][:10]

        if not fallback_insights:
            fallback_insights = [
                "Analysis was performed but results could not be structured."
            ]

        return {
            "insights": fallback_insights,
            "logs": [
                f"[{timestamp}] ⚠️ Analyst: JSON parsing failed, "
                f"extracted {len(fallback_insights)} insights from raw text"
            ],
        }

    except Exception as e:
        logger.error(f"[Analyst] Error: {e}")
        return {
            "insights": [f"Analysis encountered an error: {str(e)}"],
            "logs": [
                f"[{timestamp}] ❌ Analyst: Error during analysis: {e}"
            ],
        }
