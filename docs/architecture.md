# Architecture Documentation

## High-Level Design (HLD)

```
┌──────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                 Streamlit Frontend                  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────┐   │ │
│  │  │ Sidebar  │ │  Search  │ │  Results (Tabs)    │   │ │
│  │  │ History  │ │  Input   │ │  Plan|Sources|     │   │ │
│  │  │ Setting  │ │  Button  │ │  Insights|Summary| │   │ │
│  │  │ Status   │ │          │ │  Report|Export     │   │ │
│  │  └──────────┘ └──────────┘ └────────────────────┘   │ │
│  └─────────────────────────────────────────────────────┘ │
│                           │ HTTP/REST                    │
│                           ↓                              │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  FastAPI Backend                    │ │
│  │  /research  /history  /report/{id}  /export/*       │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              LangGraph StateGraph                   │ │
│  │                                                     │ │
│  │  START → [Planner] → [Researcher] → [Analyst]       │ │
│  │       → [Summarizer] → [Reporter] → [Memory] → END  │ │
│  │                                                     │ │
│  │  State: ResearchState (TypedDict)                   │ │
│  │  Reducer: operator.add for logs accumulation        │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                   │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │  OpenRouter  │ │  DuckDuckGo  │ │   Wikipedia     │   │
│  │  LLM API     │ │  Search API  │ │   API           │   │
│  │              │ │              │ │                 │   │
│  │  gemma-3-27b │ └──────────────┘ └─────────────────┘   │
│  │  nemotron-vl │                                        │
│  └──────────────┘                                        │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │  JSON Memory │ │  PDF Export  │ │  MD Export      │   │
│  │  (File-based)│ │  (fpdf2)     │ │  (File-based)   │   │
│  └──────────────┘ └──────────────┘ └─────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## Low-Level Design (LLD)

### State Flow

```
ResearchState {
    user_query:      str              ─── Set by user input
    research_plan:   dict             ─── Set by Planner
    search_results:  list[dict]       ─── Set by Researcher
    sources:         list[dict]       ─── Set by Researcher, updated by Analyst
    insights:        list[str]        ─── Set by Analyst
    summary:         str              ─── Set by Summarizer
    final_report:    str              ─── Set by Reporter
    memory:          dict             ─── Set by Memory Saver
    logs:            list[str]        ─── Accumulated via operator.add reducer
    model:           str              ─── Set by user (optional)
    session_id:      str              ─── Auto-generated UUID
}
```

### Node Specifications

| Node | Input Fields | Output Fields | LLM Call | Tool Call |
|------|-------------|---------------|----------|-----------|
| Planner | user_query | research_plan, logs | ✅ JSON mode | ❌ |
| Researcher | research_plan | search_results, sources, logs | ❌ | ✅ DDG + Wiki |
| Analyst | search_results, user_query | insights, sources (reranked), logs | ✅ JSON mode | ✅ Reranker |
| Summarizer | insights, user_query | summary, logs | ✅ Text mode | ❌ |
| Reporter | all fields | final_report, logs | ✅ Text mode | ❌ |
| Memory | all fields | memory, logs | ❌ | ✅ File I/O |

### Sequence Diagram

```
User                Streamlit          FastAPI           LangGraph
  │                    │                  │                  │
  │─── Enter topic ──→ │                  │                  │
  │                    │── POST /research→│                  │
  │                    │                  │── run_research()→│
  │                    │                  │                  │── planner_node()
  │                    │                  │                  │   └── LLM → plan
  │                    │                  │                  │── researcher_node()
  │                    │                  │                  │   └── DDG + Wiki
  │                    │                  │                  │── analyst_node()
  │                    │                  │                  │   ├── Reranker
  │                    │                  │                  │   └── LLM → insights
  │                    │                  │                  │── summarizer_node()
  │                    │                  │                  │   └── LLM → summary
  │                    │                  │                  │── reporter_node()
  │                    │                  │                  │   └── LLM → report
  │                    │                  │                  │── memory_saver_node()
  │                    │                  │                  │   └── JSON → disk
  │                    │                  │←── final state ──│
  │                    │←── JSON response─│                  │
  │←── Display results─│                  │                  │
```

### Error Handling Strategy

1. **LLM Failures**: Each agent has fallback logic. If JSON parsing fails, raw text is used.
2. **Search Failures**: Individual source failures are logged; other sources continue.
3. **Reranker Failures**: Original search results are used without reranking.
4. **Memory Failures**: Error is logged but doesn't block the pipeline.
5. **Export Failures**: HTTP 500 with descriptive error message.

### Security Model

- API keys in `.env` only (never in code or git)
- Session IDs sanitized against path traversal
- Pydantic validates all API inputs
- CORS scoped for frontend access
