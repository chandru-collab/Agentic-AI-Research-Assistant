"""
Report Viewer Component.

Displays research results in a tabbed interface with
plan, sources, insights, summary, and full report tabs.
"""

from __future__ import annotations

import streamlit as st


def render_report(result: dict) -> None:
    """
    Render the research results in a tabbed view.

    Parameters
    ----------
    result : dict
        Full research response from the API.
    """
    if not result or result.get("error"):
        st.error(f"❌ {result.get('error', 'Unknown error')}")
        return

    tabs = st.tabs([
        "📋 Research Plan",
        "🔍 Sources",
        "💡 Insights",
        "📝 Summary",
        "📄 Full Report",
    ])

    # ── Tab 1: Research Plan ──
    with tabs[0]:
        plan = result.get("research_plan", {})
        if plan:
            st.markdown("#### 🎯 Objectives")
            for obj in plan.get("objectives", []):
                st.markdown(f"- {obj}")

            st.markdown("#### 📂 Sub-Topics")
            for topic in plan.get("sub_topics", []):
                st.markdown(f"- {topic}")

            st.markdown("#### 🔎 Search Queries")
            for query in plan.get("search_queries", []):
                st.markdown(f"- `{query}`")
        else:
            st.info("No research plan available.")

    # ── Tab 2: Sources ──
    with tabs[1]:
        sources = result.get("sources", [])
        if sources:
            st.markdown(f"**{len(sources)} sources found**")
            st.divider()

            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "#")
                src_type = source.get("source", "unknown")
                score = source.get("relevance_score")

                # Source badge color
                badge_color = "#4ade80" if src_type == "wikipedia" else "#60a5fa"

                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(
                        f"**{i}. [{title}]({url})**"
                    )
                with col2:
                    st.markdown(
                        f'<span style="background:{badge_color};color:#000;'
                        f'padding:2px 8px;border-radius:12px;font-size:0.7rem;">'
                        f'{src_type}</span>',
                        unsafe_allow_html=True,
                    )
                if score is not None:
                    st.caption(f"Relevance: {score:.2f}")
                st.divider()
        else:
            st.info("No sources available.")

    # ── Tab 3: Insights ──
    with tabs[2]:
        insights = result.get("insights", [])
        if insights:
            st.markdown(f"**{len(insights)} key insights extracted**")
            st.divider()
            for i, insight in enumerate(insights, 1):
                st.markdown(
                    f"""<div style="
                        background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
                        border-left: 3px solid #667eea;
                        padding: 12px 16px;
                        border-radius: 0 8px 8px 0;
                        margin-bottom: 10px;
                    ">
                        <strong style="color:#667eea;">#{i}</strong> {insight}
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No insights available.")

    # ── Tab 4: Summary ──
    with tabs[3]:
        summary = result.get("summary", "")
        if summary:
            st.markdown(summary)
        else:
            st.info("No summary available.")

    # ── Tab 5: Full Report ──
    with tabs[4]:
        report = result.get("final_report", "")
        if report:
            st.markdown(report)
        else:
            st.info("No report available.")
