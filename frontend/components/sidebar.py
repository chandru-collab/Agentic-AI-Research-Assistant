"""
Sidebar Component.

Renders the sidebar with research history, settings, and model selection.
"""

from __future__ import annotations

import streamlit as st
from frontend.utils.api_client import APIClient


def render_sidebar(api: APIClient) -> dict:
    """
    Render the sidebar and return selected settings.

    Returns
    -------
    dict
        Settings with keys: model, temperature, backend_url.
    """
    with st.sidebar:
        # ── Logo / Title ──
        st.markdown(
            """
            <div style="text-align:center; padding: 10px 0 20px 0;">
                <h2 style="
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.5rem;
                    margin: 0;
                ">🔬 AI Research Assistant</h2>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">
                    Powered by LangGraph & OpenRouter
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Settings ──
        st.markdown("### ⚙️ Settings")

        model = st.selectbox(
            "LLM Model",
            options=[
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ],
            index=0,
            help="Select the Groq model for text generation",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Higher = more creative, Lower = more focused",
        )

        st.divider()

        # ── Backend Status ──
        st.markdown("### 🔌 Backend Status")
        health = api.health_check()
        if health.get("status") == "healthy":
            st.success("✅ Backend Connected", icon="🟢")
        elif health.get("status") == "in-process":
            st.info("ℹ️ Local In-Process Mode", icon="🔵")
            st.caption("Running in-process without separate backend server")
        else:
            st.error("❌ Backend Unreachable", icon="🔴")
            st.caption("Start the backend with:")
            st.code("python -m uvicorn backend.main:app --reload", language="bash")

        st.divider()

        # ── Research History ──
        st.markdown("### 📜 Research History")
        history = api.get_history()

        if not history:
            st.caption("No research sessions yet.")
        else:
            for item in history[:10]:
                session_id = item.get("session_id", "")
                query = item.get("query", "Unknown")
                created = item.get("created_at", "")[:10]

                if st.button(
                    f"📄 {query[:35]}{'...' if len(query) > 35 else ''}",
                    key=f"hist_{session_id}",
                    use_container_width=True,
                ):
                    st.session_state["load_session_id"] = session_id
                    st.rerun()

                st.caption(f"   {created}")

        st.divider()

        # ── About ──
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0; color: #666; font-size: 0.75rem;">
                <p>v1.0.0 • Built with ❤️</p>
                <p>FastAPI • LangGraph • Streamlit</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "model": model,
        "temperature": temperature,
    }
