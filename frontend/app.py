"""
Streamlit Frontend — AI Research Assistant.

Premium dark-themed UI with research input, progress tracking,
tabbed results, execution logs, and export capabilities.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path

# Add project root to path so we can import frontend modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.progress import render_progress
from frontend.components.report_viewer import render_report
from frontend.components.log_viewer import render_logs

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS — Premium Dark Theme
# ──────────────────────────────────────────────

st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero gradient title */
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        text-align: center;
        color: #888;
        font-size: 1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Search container */
    .search-container {
        background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
        border: 1px solid rgba(102,126,234,0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Result cards */
    .result-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }

    .result-card:hover {
        border-color: rgba(102,126,234,0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(102,126,234,0.15);
    }

    /* Export buttons */
    .export-section {
        background: linear-gradient(135deg, rgba(74,222,128,0.08), rgba(96,165,250,0.08));
        border: 1px solid rgba(74,222,128,0.2);
        border-radius: 12px;
        padding: 16px;
        margin-top: 16px;
    }

    /* Pulse animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Stats cards */
    .stat-card {
        background: rgba(102,126,234,0.1);
        border: 1px solid rgba(102,126,234,0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }

    .stat-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Initialize State
# ──────────────────────────────────────────────

if "research_result" not in st.session_state:
    st.session_state.research_result = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "load_session_id" not in st.session_state:
    st.session_state.load_session_id = None

api = APIClient()


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

sidebar_settings = render_sidebar(api)


# ──────────────────────────────────────────────
# Load session from history (if clicked)
# ──────────────────────────────────────────────

if st.session_state.load_session_id:
    session_id = st.session_state.load_session_id
    st.session_state.load_session_id = None  # Reset

    with st.spinner("Loading previous research..."):
        report_data = api.get_report(session_id)
        if not report_data.get("error"):
            st.session_state.research_result = report_data


# ──────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────

# Hero Section
st.markdown('<h1 class="hero-title">🔬 AI Research Assistant</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">'
    'Enter any topic and let AI agents research, analyze, and generate a comprehensive report'
    '</p>',
    unsafe_allow_html=True,
)

# ── Search Section ──
st.markdown('<div class="search-container">', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        "Research Topic",
        placeholder="e.g., Research Agentic AI, Quantum Computing Applications, Climate Change Solutions...",
        label_visibility="collapsed",
        key="research_input",
    )

with col2:
    research_clicked = st.button(
        "🚀 Research",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.is_researching,
    )

st.markdown('</div>', unsafe_allow_html=True)


# ── Run Research ──
if research_clicked and query:
    st.session_state.is_researching = True
    st.session_state.research_result = None

    # Progress section
    st.markdown("### 🔄 Research Pipeline")
    render_progress(current_step=0)

    progress_placeholder = st.empty()

    with st.spinner("🔬 Running research pipeline... This may take 1-3 minutes."):
        result = api.run_research(
            query=query,
            model=sidebar_settings.get("model"),
        )

    st.session_state.is_researching = False

    if result.get("error"):
        st.error(f"❌ Research failed: {result['error']}")
    else:
        st.session_state.research_result = result
        st.rerun()


# ── Display Results ──
if st.session_state.research_result and not st.session_state.is_researching:
    result = st.session_state.research_result

    # Completed progress
    st.markdown("### ✅ Research Complete")
    render_progress(is_complete=True)

    st.divider()

    # ── Stats Row ──
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sources_count = len(result.get("sources", []))
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{sources_count}</div>
                <div class="stat-label">Sources</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col2:
        insights_count = len(result.get("insights", []))
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{insights_count}</div>
                <div class="stat-label">Insights</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col3:
        report_len = len(result.get("final_report", ""))
        word_count = len(result.get("final_report", "").split())
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{word_count:,}</div>
                <div class="stat-label">Words</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col4:
        log_count = len(result.get("logs", []))
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{log_count}</div>
                <div class="stat-label">Steps</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Report Viewer (Tabbed) ──
    render_report(result)

    st.divider()

    # ── Execution Logs ──
    render_logs(result.get("logs", []))

    # ── Export Section ──
    st.markdown("### ⬇️ Export Report")

    session_id = result.get("session_id", "")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Download PDF", use_container_width=True, type="primary"):
            with st.spinner("Generating PDF..."):
                pdf_bytes = api.export_pdf(session_id)
                if pdf_bytes:
                    query_name = result.get("query", "research")[:30]
                    st.download_button(
                        label="💾 Save PDF",
                        data=pdf_bytes,
                        file_name=f"{query_name}_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("PDF generation failed")

    with col2:
        if st.button("📥 Download Markdown", use_container_width=True):
            with st.spinner("Generating Markdown..."):
                md_content = api.export_markdown(session_id)
                if md_content:
                    query_name = result.get("query", "research")[:30]
                    st.download_button(
                        label="💾 Save Markdown",
                        data=md_content,
                        file_name=f"{query_name}_report.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                else:
                    st.error("Markdown generation failed")

elif not st.session_state.is_researching:
    # ── Empty State ──
    st.markdown("---")

    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px; color: #666;">
            <div style="font-size: 4rem; margin-bottom: 16px;">🔬</div>
            <h3 style="color: #888; font-weight: 400;">Ready to Research</h3>
            <p style="max-width: 500px; margin: 0 auto; line-height: 1.6;">
                Enter any research topic above and click <strong>Research</strong>.
                The AI will plan, search, analyze, summarize, and generate
                a comprehensive report with citations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    st.markdown("---")
    st.markdown("### ✨ Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="result-card">
                <h4>📋 Smart Planning</h4>
                <p style="color:#888; font-size:0.85rem;">
                    AI creates a structured research plan with objectives,
                    sub-topics, and optimized search queries.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="result-card">
                <h4>🔍 Multi-Source Search</h4>
                <p style="color:#888; font-size:0.85rem;">
                    Searches DuckDuckGo and Wikipedia simultaneously,
                    with vision-based relevance reranking.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="result-card">
                <h4>📄 Professional Reports</h4>
                <p style="color:#888; font-size:0.85rem;">
                    Generates detailed reports with citations,
                    exportable as PDF or Markdown.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
