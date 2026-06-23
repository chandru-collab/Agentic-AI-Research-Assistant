# 🔬 Agentic AI Research Assistant

A production-ready, multi-agent research assistant powered by **LangGraph**, **FastAPI**, and **React + Vite**. Enter any research topic and the system will autonomously plan, search, analyze, summarize, and generate a comprehensive report with citations.

---

## ✨ Features

### 🤖 Agentic Capabilities
- **Multi-step reasoning** — LangGraph orchestrates a pipeline of specialized agents
- **Tool calling** — DuckDuckGo + Wikipedia search integration
- **Smart planning** — AI creates structured research strategies
- **Vision reranking** — NVIDIA Nemotron reranker scores document relevance
- **Source citation** — All findings are tracked back to their sources
- **Memory** — JSON-based persistent session storage

### 📄 Export
- **PDF Export** — Professional styled reports with headers, citations, and formatting
- **Markdown Export** — Clean Markdown with YAML frontmatter

### 🎨 User Experience
- **Premium React + Vite UI** — Dark theme with neon-glowing animations and modern glassmorphism
- **Progress tracking** — Real-time pipeline step visualization
- **Execution logs** — Color-coded log viewer
- **History viewer** — Browse and reload past research sessions

---

## 🏗️ Architecture

```
User → Streamlit UI → FastAPI Backend → LangGraph Workflow
                                              │
                    ┌─────────────────────────┤
                    ↓                         ↓
              Planner Agent            Memory Manager
                    ↓
              Research Agent (DuckDuckGo + Wikipedia)
                    ↓
              Analysis Agent 
                    ↓
              Summary Agent
                    ↓
              Report Generator
                    ↓
              Final Response → Export (PDF / Markdown)
```

### LangGraph Workflow

```
START → Planner → Researcher → Analyst → Summarizer → Reporter → Memory → END
```

Each node is an async function that receives the full typed state and returns a partial update.

---

## 📁 Project Structure

```
agentic ai project/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment configuration
│   ├── api/routes.py            # REST API endpoints
│   ├── schemas/
│   │   ├── state.py             # LangGraph TypedDict state
│   │   └── models.py            # Pydantic request/response models
│   ├── services/
│   │   ├── llm_service.py       # OpenRouter LLM wrapper
│   │   └── reranker_service.py  # NVIDIA vision reranker
│   ├── tools/search_tools.py    # DuckDuckGo + Wikipedia
│   ├── agents/
│   │   ├── planner.py           # Research planning
│   │   ├── researcher.py        # Web searching
│   │   ├── analyst.py           # Insight extraction
│   │   ├── summarizer.py        # Executive summary
│   │   └── reporter.py          # Report generation
│   ├── graph/workflow.py        # LangGraph StateGraph
│   ├── memory/memory_manager.py # JSON session storage
│   └── export/
│       ├── pdf_export.py        # PDF generation (fpdf2)
│       └── markdown_export.py   # Markdown export
├── frontend/
│   ├── app.py                   # Streamlit main app
│   ├── components/              # UI components
│   └── utils/api_client.py      # Backend HTTP client
├── tests/                       # pytest test suite
├── reports/                     # Generated reports
├── memory/                      # Session JSON files
├── docs/                        # Architecture docs
├── .env                         # API keys (git-ignored)
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An [OpenRouter](https://openrouter.ai/) API key

### 1. Clone & Setup

```bash
git clone <repo-url>
cd "agentic ai project"

# Create virtual environment
uv venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DEFAULT_MODEL=google/gemma-3-27b-it:free
RERANKER_MODEL=nvidia/llama-nemotron-rerank-vl-1b-v2:free
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 4. Start the Backend

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### 6. Open in Browser

Navigate to `http://localhost:5173` and start researching!

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/research` | Execute full research workflow |
| `GET` | `/history` | List all past sessions |
| `GET` | `/report/{id}` | Get a specific report |
| `POST` | `/export/pdf` | Download PDF report |
| `POST` | `/export/markdown` | Download Markdown report |
| `GET` | `/health` | Health check |

### Example: Run Research

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Research Agentic AI"}'
```

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Agent Framework | LangGraph |
| LLM | OpenRouter API |
| Search | DuckDuckGo + Wikipedia |
| Vision Reranking | NVIDIA Nemotron VL |
| Memory | JSON File Storage |
| PDF Export | fpdf2 |
| Validation | Pydantic v2 |
| HTTP Client | httpx |
| Retry Logic | tenacity |

---

## 🔒 Security

- API keys stored in `.env` (git-ignored)
- Path traversal protection in memory manager
- Input validation via Pydantic
- CORS configured for frontend access

---

## 🚀 Future Enhancements

- [ ] Streaming responses via WebSocket
- [ ] PostgreSQL/Redis for production memory
- [ ] User authentication (OAuth2)
- [ ] Concurrent agent execution
- [ ] Custom source integrations (arXiv, Google Scholar)
- [ ] Report templates and customization
- [ ] Docker containerization
- [ ] CI/CD pipeline

---

## 📄 License

MIT License

---

*Built with ❤️ using LangGraph, FastAPI, and Streamlit*
