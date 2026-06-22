"""
Researcher Agent Node.

Executes search queries from the research plan across
DuckDuckGo and Wikipedia, collecting raw results and sources.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.tools.search_tools import search_all

logger = logging.getLogger(__name__)


async def researcher_node(state: dict) -> dict:
    """
    Researcher node for the LangGraph workflow.

    Takes the research_plan from state, executes search queries
    across all configured sources.

    Parameters
    ----------
    state : dict
        Current workflow state with 'research_plan'.

    Returns
    -------
    dict
        Partial state update with 'search_results', 'sources', and 'logs'.
    """
    research_plan = state.get("research_plan", {})
    search_queries = research_plan.get("search_queries", [])
    user_query = state.get("user_query", "")
    timestamp = datetime.now(timezone.utc).isoformat()

    if not search_queries:
        search_queries = [user_query]

    logger.info(
        f"[Researcher] Executing {len(search_queries)} search queries"
    )

    import asyncio

    all_results: list[dict] = []
    all_sources: list[dict] = []
    seen_urls: set[str] = set()

    # Semaphore to cap concurrent search requests to prevent API rate limits
    sem = asyncio.Semaphore(3)

    async def run_query(query: str, index: int) -> tuple[int, str, list[dict]]:
        async with sem:
            logger.info(
                f"[Researcher] Executing query {index + 1}/{len(search_queries)}: '{query}'"
            )
            try:
                results = await search_all(
                    query=query,
                    ddg_max=5,
                    wiki_max=2,
                )
                return index, query, results
            except Exception as e:
                logger.warning(f"[Researcher] Search failed for '{query}': {e}")
                return index, query, []

    # Run queries concurrently
    tasks = [run_query(q, i) for i, q in enumerate(search_queries)]
    completed = await asyncio.gather(*tasks)

    # Sort by query index for deterministic output order matching the original design
    completed.sort(key=lambda x: x[0])

    for _, query, results in completed:
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(result)
                all_sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": url,
                    "source": result.get("source", "unknown"),
                    "query": query,
                })
            elif not url:
                all_results.append(result)

    logger.info(
        f"[Researcher] Collected {len(all_results)} unique results "
        f"from {len(search_queries)} queries"
    )

    return {
        "search_results": all_results,
        "sources": all_sources,
        "logs": [
            f"[{timestamp}] 🔍 Researcher: Executed {len(search_queries)} queries, "
            f"collected {len(all_results)} unique results from "
            f"{len(all_sources)} sources"
        ],
    }
