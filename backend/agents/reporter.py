"""
Reporter Agent Node.

Generates a comprehensive, professional research report
with citations, table of contents, and structured sections.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.services.llm_service import invoke_llm

logger = logging.getLogger(__name__)

REPORTER_SYSTEM_PROMPT = """You are an expert report writer. Your job is to compile research findings
into a professional, publication-quality research report.

Create a comprehensive Markdown report with the following structure:

# [Research Topic] — Research Report

**Generated:** [Date]
**Sources Consulted:** [Number]

---

## Table of Contents
1. Introduction
2. Research Objectives
3. Methodology
4. Key Findings
5. Detailed Analysis
6. Trends & Patterns
7. Challenges & Limitations
8. Future Outlook
9. Conclusion
10. References

---

## 1. Introduction
[2-3 paragraph introduction]

## 2. Research Objectives
[Bullet list of objectives from the plan]

## 3. Methodology
[Brief description of research methodology]

## 4. Key Findings
[Numbered list of major findings]

## 5. Detailed Analysis
[In-depth analysis organized by sub-topic with subsections]

## 6. Trends & Patterns
[Observed trends and emerging patterns]

## 7. Challenges & Limitations
[Current challenges and research limitations]

## 8. Future Outlook
[Predictions and future directions]

## 9. Conclusion
[Summary conclusion]

## 10. References
[Numbered list of all sources with URLs]

Guidelines:
- Use professional, academic writing style
- Include specific data points and examples from the research
- Cite sources using [Source N] notation
- Create a thorough, informative report (1500-3000 words)
- Use proper Markdown formatting with headers, lists, bold, etc.
"""


async def reporter_node(state: dict) -> dict:
    """
    Reporter node for the LangGraph workflow.

    Compiles all gathered information into a professional report.

    Parameters
    ----------
    state : dict
        Current workflow state with all research data.

    Returns
    -------
    dict
        Partial state update with 'final_report' and 'logs'.
    """
    user_query = state.get("user_query", "")
    research_plan = state.get("research_plan", {})
    insights = state.get("insights", [])
    summary = state.get("summary", "")
    sources = state.get("sources", [])
    model = state.get("model")
    timestamp = datetime.now(timezone.utc).isoformat()
    report_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Format all data for the prompt
    objectives_text = "\n".join(
        f"  - {obj}"
        for obj in research_plan.get("objectives", ["General research"])
    )
    sub_topics_text = "\n".join(
        f"  - {st}"
        for st in research_plan.get("sub_topics", [user_query])
    )
    insights_text = "\n".join(
        f"  {i + 1}. {insight}" for i, insight in enumerate(insights)
    )
    sources_text = "\n".join(
        f"  [{i + 1}] {s.get('title', 'Untitled')} — {s.get('url', 'N/A')} "
        f"(Source: {s.get('source', 'unknown')})"
        for i, s in enumerate(sources)
    )

    prompt = f"""Compile a comprehensive research report for the following topic.

RESEARCH TOPIC: {user_query}
REPORT DATE: {report_date}

RESEARCH OBJECTIVES:
{objectives_text}

SUB-TOPICS INVESTIGATED:
{sub_topics_text}

KEY INSIGHTS:
{insights_text}

EXECUTIVE SUMMARY:
{summary}

SOURCES ({len(sources)} total):
{sources_text}

Generate a complete, professional research report in Markdown format.
Include all sections listed in the guidelines.
Cite sources using [Source N] notation throughout the report.
The report should be thorough (1500-3000 words)."""

    try:
        report = await invoke_llm(
            prompt=prompt,
            model=model,
            system_prompt=REPORTER_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=8192,
        )

        if not report or not report.strip():
            report = _generate_fallback_report(
                user_query, research_plan, insights, summary, sources, report_date
            )

        logger.info(
            f"[Reporter] Generated report ({len(report)} chars) "
            f"with {len(sources)} source citations"
        )

        return {
            "final_report": report.strip(),
            "logs": [
                f"[{timestamp}] 📄 Reporter: Generated comprehensive report "
                f"({len(report)} chars) with {len(sources)} citations"
            ],
        }

    except Exception as e:
        logger.error(f"[Reporter] Error: {e}")
        fallback = _generate_fallback_report(
            user_query, research_plan, insights, summary, sources, report_date
        )
        return {
            "final_report": fallback,
            "logs": [
                f"[{timestamp}] ⚠️ Reporter: Error ({e}), "
                f"generated structured fallback report"
            ],
        }


def _generate_fallback_report(
    query: str,
    plan: dict,
    insights: list[str],
    summary: str,
    sources: list[dict],
    date: str,
) -> str:
    """Generate a structured fallback report when LLM fails."""
    report = f"# {query} — Research Report\n\n"
    report += f"**Generated:** {date}\n"
    report += f"**Sources Consulted:** {len(sources)}\n\n"
    report += "---\n\n"

    report += "## Research Objectives\n\n"
    for obj in plan.get("objectives", [f"Research {query}"]):
        report += f"- {obj}\n"
    report += "\n"

    report += "## Executive Summary\n\n"
    report += f"{summary}\n\n"

    report += "## Key Findings\n\n"
    for i, insight in enumerate(insights, 1):
        report += f"{i}. {insight}\n\n"

    report += "## References\n\n"
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "N/A")
        src = source.get("source", "unknown")
        report += f"[{i}] {title} — {url} ({src})\n\n"

    report += "\n---\n*Report generated by AI Research Assistant*\n"
    return report
