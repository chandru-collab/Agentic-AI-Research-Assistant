"""Quick verification script for the enhanced PDF export."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.export.pdf_export import get_pdf_bytes

sample_session = {
    "session_id": "verify-test-001",
    "user_query": "Agentic AI Research: Current State and Future Directions",
    "research_plan": {
        "objectives": ["Understand agentic AI", "Identify trends"],
        "sub_topics": ["LLM Agents", "Tool Use", "Multi-Agent Systems"],
        "search_queries": ["agentic AI 2025", "LLM agent frameworks"],
    },
    "sources": [
        {"title": "LangChain Documentation", "url": "https://docs.langchain.com", "snippet": "LangChain is a framework for developing applications powered by language models.", "source": "duckduckgo"},
        {"title": "AutoGPT GitHub", "url": "https://github.com/Significant-Gravitas/AutoGPT", "snippet": "AutoGPT is an experimental open-source autonomous AI agent.", "source": "duckduckgo"},
        {"title": "Wikipedia: AI Agent", "url": "https://en.wikipedia.org/wiki/Intelligent_agent", "snippet": "An intelligent agent is an autonomous entity that acts upon an environment.", "source": "wikipedia"},
    ],
    "insights": [
        "Agentic AI is rapidly evolving with new frameworks emerging monthly",
        "Tool use capability is a key differentiator",
        "Multi-agent collaboration shows promise for complex tasks",
    ],
    "summary": "Comprehensive overview of agentic AI landscape in 2025.",
    "final_report": """# Agentic AI Research: Current State and Future Directions

## Executive Summary

This report provides a **comprehensive analysis** of the *agentic AI* landscape, covering recent advancements, key frameworks, and future directions. The research draws from multiple sources including academic papers, industry reports, and open-source projects.

> Agentic AI represents a paradigm shift in how we interact with and deploy artificial intelligence systems, moving from passive tools to active collaborators.

## Key Findings

1. **Framework Proliferation**: Over 15 major agentic AI frameworks launched in 2024-2025
2. **Enterprise Adoption**: 40% of Fortune 500 companies are piloting agentic AI
3. *Research Investment*: Global R&D spending on AI agents exceeded $12B

## Market Overview

| Category | Market Size | YoY Growth | Key Players |
|----------|------------|------------|-------------|
| LLM Agents | $8.2B | +45% | OpenAI, Google, Anthropic |
| Tool Use | $3.1B | +62% | LangChain, CrewAI |
| Multi-Agent | $1.8B | +78% | AutoGen, MetaGPT |
| Evaluation | $0.9B | +35% | Braintrust, Langfuse |

## Technical Architecture

Modern agentic AI systems typically follow a **ReAct** (Reasoning + Acting) pattern:

- Observe the current state and user intent
- Reason about what actions to take
  - Consider available tools and their capabilities
  - Evaluate potential outcomes
- Act by executing the chosen tool or generating a response
- Reflect on the outcome and update internal state

## Implementation Approaches

### LangGraph Pipeline

```python
from langgraph.graph import StateGraph

graph = StateGraph(ResearchState)
graph.add_node("planner", plan_research)
graph.add_node("researcher", search_sources)
graph.add_node("analyst", analyze_findings)
```

### Key Design Patterns

1. **State Machine**: Explicit state transitions with typed state objects
2. **Tool Registry**: Dynamic tool discovery and execution
3. **Memory Systems**: Short-term and long-term memory for context retention
4. **Evaluation Loops**: Built-in quality checks and self-correction

## Challenges and Limitations

- Hallucination remains a significant concern in autonomous systems
- Cost of running multi-step agent workflows can be prohibitive
- Security implications of tool-using agents need careful consideration
  - Sandboxing and permission systems are essential
  - Audit trails must be maintained

> The biggest challenge is not building agents that can act, but building agents that know when NOT to act.

---

## Conclusion

Agentic AI is transforming the software landscape. Organizations that invest in understanding and deploying these systems will gain significant competitive advantages. The key is to start with well-defined, bounded use cases and expand as confidence and capability grow.

## References

[1] LangChain Documentation - https://docs.langchain.com
[2] AutoGPT GitHub - https://github.com/Significant-Gravitas/AutoGPT
[3] Wikipedia: AI Agent - https://en.wikipedia.org/wiki/Intelligent_agent
""",
    "created_at": "2025-06-23T12:00:00Z",
    "logs": ["Step 1: Planning", "Step 2: Researching", "Step 3: Analyzing"],
}

print("Generating enhanced PDF...")
pdf_bytes = get_pdf_bytes(sample_session)
print(f"PDF generated successfully!")
print(f"  Size: {len(pdf_bytes):,} bytes")
print(f"  Magic: {pdf_bytes[:4]}")

# Save to reports dir for manual inspection
output_path = project_root / "reports" / "verify_enhanced_report.pdf"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_bytes(pdf_bytes)
print(f"  Saved to: {output_path}")
print("PASS")
