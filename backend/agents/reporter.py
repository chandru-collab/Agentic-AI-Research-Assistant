"""
Reporter Agent Node.

Generates a comprehensive, professional research report
with citations, tables, infographics, and structured sections.
Enhanced to produce clear, accurate, fact-based content with
rich markdown formatting (tables, bullet points, blockquotes).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.services.llm_service import invoke_llm

logger = logging.getLogger(__name__)

REPORTER_SYSTEM_PROMPT = """You are a world-class research report writer who produces publication-quality,
fact-based research reports. Your reports are known for their clarity, accuracy, and visual richness.

CRITICAL RULES FOR ACCURACY:
- ONLY include facts, data, and claims that are directly supported by the provided sources and insights
- NEVER fabricate statistics, percentages, dates, or claims not found in the research data
- If the data is insufficient for a section, state "Based on available research..." rather than inventing facts
- Use hedging language ("research suggests", "evidence indicates") rather than absolute claims when appropriate
- Every major claim must reference a source using [Source N] notation
- Clearly distinguish between established facts and emerging trends/opinions

REPORT STRUCTURE — Use this exact format:

# [Research Topic] — Research Report

**Generated:** [Date]
**Sources Consulted:** [Number]
**Research Scope:** [Brief 1-line scope statement]

---

## Executive Summary

> [2-3 sentence blockquote capturing the most important takeaway from this research]

[1-2 paragraph overview of what the research found — concise, factual, no filler]

## Key Findings at a Glance

| # | Finding | Significance |
|---|---------|-------------|
| 1 | [Finding 1] | [Why it matters] |
| 2 | [Finding 2] | [Why it matters] |
| 3 | [Finding 3] | [Why it matters] |

## Research Objectives

- [Objective 1 — derived from the research plan]
- [Objective 2]
- [Objective 3]

## Detailed Analysis

### [Sub-topic 1 Title]

[2-3 paragraphs of clear, factual analysis for this sub-topic.
Include specific data points from the sources.
Use **bold** for key terms and *italic* for emphasis.]

### [Sub-topic 2 Title]

[Similar detailed analysis]

## Comparative Overview

| Aspect | Current State | Trend | Source |
|--------|--------------|-------|--------|
| [Aspect 1] | [Description] | [Direction] | [Source N] |
| [Aspect 2] | [Description] | [Direction] | [Source N] |

## Challenges & Limitations

1. **[Challenge 1]**: [Clear explanation with evidence]
2. **[Challenge 2]**: [Clear explanation with evidence]
3. **[Challenge 3]**: [Clear explanation with evidence]

## Future Outlook

> [Key prediction or forward-looking statement as a blockquote]

- [Trend/prediction 1 with supporting reasoning]
- [Trend/prediction 2 with supporting reasoning]

## Conclusion

[2-3 paragraph conclusion that ties everything together.
Be specific — reference the most important findings.
End with actionable implications.]

## References

[1] [Full source citation with title and URL]
[2] [Full source citation]
...

FORMATTING GUIDELINES:
- Use markdown tables (| col1 | col2 |) for comparative data — include AT LEAST 2 tables
- Use blockquotes (> text) for key insights and important callouts — use AT LEAST 2
- Use bullet points (-) for lists of items, features, or findings
- Use numbered lists (1. 2. 3.) for sequential or ranked items
- Use **bold** for key terms, definitions, and important phrases
- Use *italic* for emphasis, caveats, or secondary information
- Use --- for section dividers where appropriate
- Use ### for sub-section headings within main sections
- Write 1500-3000 words of substantive, clear content
- Every paragraph should convey specific, useful information — NO filler text
- Use code blocks (```) for technical terms, commands, or data formats if relevant
"""


async def reporter_node(state: dict) -> dict:
    """
    Reporter node for the LangGraph workflow.

    Compiles all gathered information into a professional,
    infographic-rich report with tables, blockquotes, and structured data.

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
        f"(Source: {s.get('source', 'unknown')})\n"
        f"       Snippet: {s.get('snippet', s.get('relevance_score', 'N/A'))}"
        for i, s in enumerate(sources)
    )

    prompt = f"""Compile a comprehensive, accurate, and visually rich research report for the following topic.

RESEARCH TOPIC: {user_query}
REPORT DATE: {report_date}

RESEARCH OBJECTIVES:
{objectives_text}

SUB-TOPICS INVESTIGATED:
{sub_topics_text}

KEY INSIGHTS (verified from sources):
{insights_text}

EXECUTIVE SUMMARY:
{summary}

SOURCES ({len(sources)} total):
{sources_text}

CRITICAL INSTRUCTIONS:
1. Generate a complete, professional research report following the exact structure in your guidelines
2. ONLY state facts and data that are supported by the insights and sources above
3. Include AT LEAST 2 markdown tables with real data from the research
4. Include AT LEAST 2 blockquotes (> ) highlighting key findings
5. Use bullet points, numbered lists, and bold/italic formatting throughout
6. Cite every major claim with [Source N] notation
7. If data is insufficient for a claim, say "Based on available research..." — DO NOT fabricate
8. The report should be thorough (1500-3000 words) with ZERO filler content
9. Every paragraph must convey specific, useful information"""

    try:
        report = await invoke_llm(
            prompt=prompt,
            model=model,
            system_prompt=REPORTER_SYSTEM_PROMPT,
            temperature=0.2,  # Lower temperature for more factual output
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
    """Generate a structured fallback report when LLM fails.

    Enhanced to include tables, blockquotes, and proper formatting
    even in fallback mode.
    """
    report = f"# {query} — Research Report\n\n"
    report += f"**Generated:** {date}\n"
    report += f"**Sources Consulted:** {len(sources)}\n\n"
    report += "---\n\n"

    # Executive Summary with blockquote
    report += "## Executive Summary\n\n"
    if summary:
        first_sentence = summary.split(".")[0] + "." if "." in summary else summary
        report += f"> {first_sentence}\n\n"
        report += f"{summary}\n\n"
    else:
        report += f"> Research was conducted on {query} using multiple sources.\n\n"

    # Key Findings Table
    report += "## Key Findings at a Glance\n\n"
    if insights:
        report += "| # | Finding | Category |\n"
        report += "|---|---------|----------|\n"
        for i, insight in enumerate(insights[:8], 1):
            # Truncate for table
            short = insight[:80] + "..." if len(insight) > 80 else insight
            report += f"| {i} | {short} | Research Finding |\n"
        report += "\n"

    # Research Objectives
    report += "## Research Objectives\n\n"
    for obj in plan.get("objectives", [f"Research {query}"]):
        report += f"- {obj}\n"
    report += "\n"

    # Detailed Findings
    report += "## Key Findings\n\n"
    for i, insight in enumerate(insights, 1):
        report += f"{i}. **Finding {i}**: {insight}\n\n"

    # Sources Table
    report += "## References\n\n"
    report += "| # | Source | Type | URL |\n"
    report += "|---|--------|------|-----|\n"
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")[:40]
        url = source.get("url", "N/A")
        src = source.get("source", "unknown")
        report += f"| {i} | {title} | {src} | {url} |\n"

    report += "\n---\n*Report generated by AI Research Assistant*\n"
    return report
