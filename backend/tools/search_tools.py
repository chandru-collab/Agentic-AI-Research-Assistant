"""
Search tools for gathering information from DuckDuckGo and Wikipedia.

Provides standardized search result format across all sources
with error handling and graceful fallbacks.
"""

from __future__ import annotations

import logging
from typing import Optional

import wikipedia
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


def _search_duckduckgo_sync(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                max_results=max_results,
                safesearch="moderate",
            )
            for r in search_results:
                results.append({
                    "title": r.get("title", "Untitled"),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "source": "duckduckgo",
                })

        logger.info(f"DuckDuckGo returned {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.error(f"DuckDuckGo search failed for '{query}': {e}")
        return []


async def search_duckduckgo(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Search DuckDuckGo for the given query (run in a worker thread).
    """
    import asyncio
    return await asyncio.to_thread(_search_duckduckgo_sync, query, max_results)


def _search_wikipedia_sync(
    query: str,
    max_results: int = 5,
    sentences: int = 10,
) -> list[dict]:
    try:
        import wikipedia

        results = []
        # Search for relevant article titles
        search_titles = wikipedia.search(query, results=max_results)

        for title in search_titles:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summary = wikipedia.summary(
                    title,
                    sentences=sentences,
                    auto_suggest=False,
                )
                results.append({
                    "title": page.title,
                    "url": page.url,
                    "snippet": summary,
                    "source": "wikipedia",
                })
            except wikipedia.exceptions.DisambiguationError as e:
                # Pick the first option from disambiguation
                if e.options:
                    try:
                        page = wikipedia.page(
                            e.options[0], auto_suggest=False
                        )
                        summary = wikipedia.summary(
                            e.options[0],
                            sentences=sentences,
                            auto_suggest=False,
                        )
                        results.append({
                            "title": page.title,
                            "url": page.url,
                            "snippet": summary,
                            "source": "wikipedia",
                        })
                    except Exception:
                        pass
            except wikipedia.exceptions.PageError:
                logger.warning(f"Wikipedia page not found: {title}")
                continue
            except Exception as e:
                logger.warning(f"Wikipedia error for '{title}': {e}")
                continue

        logger.info(f"Wikipedia returned {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.error(f"Wikipedia search failed for '{query}': {e}")
        return []


async def search_wikipedia(
    query: str,
    max_results: int = 5,
    sentences: int = 10,
) -> list[dict]:
    """
    Search Wikipedia for the given query (run in a worker thread).
    """
    import asyncio
    return await asyncio.to_thread(
        _search_wikipedia_sync, query, max_results, sentences
    )


async def search_all(
    query: str,
    ddg_max: int = 10,
    wiki_max: int = 5,
) -> list[dict]:
    """
    Execute searches across all sources and combine results.

    Parameters
    ----------
    query : str
        Search query.
    ddg_max : int
        Max DuckDuckGo results.
    wiki_max : int
        Max Wikipedia results.

    Returns
    -------
    list[dict]
        Combined and deduplicated results from all sources.
    """
    import asyncio

    # Run both searches concurrently
    ddg_task = asyncio.create_task(search_duckduckgo(query, ddg_max))
    wiki_task = asyncio.create_task(search_wikipedia(query, wiki_max))

    ddg_results, wiki_results = await asyncio.gather(
        ddg_task, wiki_task, return_exceptions=True
    )

    combined = []

    if isinstance(ddg_results, list):
        combined.extend(ddg_results)
    else:
        logger.error(f"DuckDuckGo search raised: {ddg_results}")

    if isinstance(wiki_results, list):
        combined.extend(wiki_results)
    else:
        logger.error(f"Wikipedia search raised: {wiki_results}")

    # Deduplicate by URL
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for result in combined:
        url = result.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(result)
        elif not url:
            deduped.append(result)

    logger.info(
        f"Combined search: {len(deduped)} unique results "
        f"({len(combined)} total before dedup)"
    )
    return deduped
