"""
Vision Reranker Service using NVIDIA Llama-Nemotron-Rerank-VL.

Evaluates the relevance of document text/images against a user query
for vision RAG pipelines handling charts, tables, and infographics.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from backend.config import settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def rerank_documents(
    query: str,
    documents: list[dict],
    top_k: int = 5,
    model: Optional[str] = None,
) -> list[dict]:
    """
    Rerank documents using the NVIDIA vision reranker via OpenRouter.

    Evaluates document relevance against the query and returns
    sorted results. Works with both text snippets and image URLs.

    Parameters
    ----------
    query : str
        The user's research query.
    documents : list[dict]
        List of documents to rerank. Each dict should have:
        - 'content': str (text snippet)
        - 'title': str
        - 'url': str
        - 'source': str
        Optionally:
        - 'image_url': str (for vision-based reranking)
    top_k : int
        Number of top results to return.
    model : str, optional
        Reranker model override. Defaults to settings.RERANKER_MODEL.

    Returns
    -------
    list[dict]
        Documents sorted by relevance score (highest first),
        each augmented with a 'relevance_score' field.
    """
    settings.validate()
    reranker_model = model or settings.RERANKER_MODEL

    # Build messages for relevance scoring
    import asyncio

    sem = asyncio.Semaphore(4)

    async def score_doc(client: httpx.AsyncClient, doc: dict) -> dict:
        async with sem:
            # Construct the relevance evaluation prompt
            content_parts = []

            # Add image if available (for vision reranking)
            if doc.get("image_url"):
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": doc["image_url"]},
                })

            # Add text content
            text_content = (
                f"Query: {query}\n\n"
                f"Document Title: {doc.get('title', 'Untitled')}\n"
                f"Document Content: {doc.get('content', doc.get('snippet', ''))}"
            )
            content_parts.append({"type": "text", "text": text_content})

            try:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": settings.APP_NAME,
                    },
                    json={
                        "model": reranker_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": content_parts,
                            }
                        ],
                        "max_tokens": 5,
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Extract relevance signal from the response
                # The reranker model returns logits/scores
                relevance_text = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "0")
                )

                # Try to parse a numeric score; default to 0 on failure
                try:
                    score = float(relevance_text.strip().split()[0])
                except (ValueError, IndexError):
                    # Use a heuristic: if the model returned "yes"/"relevant",
                    # give higher score
                    lower_text = relevance_text.lower()
                    if any(w in lower_text for w in ("yes", "relevant", "true")):
                        score = 1.0
                    else:
                        score = 0.5

                return {**doc, "relevance_score": score}

            except Exception as e:
                logger.warning(f"Reranker failed for doc '{doc.get('title')}': {e}")
                # Assign neutral score on failure so doc isn't dropped
                return {**doc, "relevance_score": 0.5}

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [score_doc(client, doc) for doc in documents]
        scored_documents = await asyncio.gather(*tasks)

    # Sort by relevance descending and return top_k
    scored_documents = list(scored_documents)
    scored_documents.sort(key=lambda d: d.get("relevance_score", 0.5), reverse=True)
    return scored_documents[:top_k]


async def rerank_search_results(
    query: str,
    search_results: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """
    Convenience wrapper: reranks search results from search tools.

    Maps search result format → reranker format → back to search result format.
    Falls back to returning original results if reranking fails entirely.
    """
    if not search_results:
        return search_results

    try:
        # Map search results to reranker document format, limiting candidate list
        # to top 20 to save tokens, avoid rate limits and reduce latency
        documents = [
            {
                "content": r.get("snippet", ""),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": r.get("source", "unknown"),
            }
            for r in search_results[:20]
        ]

        reranked = await rerank_documents(query, documents, top_k=top_k)

        # Map back, keeping the relevance score
        return [
            {
                "title": d["title"],
                "url": d["url"],
                "snippet": d["content"],
                "source": d["source"],
                "relevance_score": d.get("relevance_score", 0.5),
            }
            for d in reranked
        ]

    except Exception as e:
        logger.error(f"Reranking failed, returning original results: {e}")
        return search_results[:top_k]
