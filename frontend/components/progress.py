"""
Progress Tracker Component.

Displays a step-by-step progress indicator for the research pipeline.
"""

from __future__ import annotations

import streamlit as st

PIPELINE_STEPS = [
    {"name": "Planning", "icon": "📋", "desc": "Creating research strategy"},
    {"name": "Searching", "icon": "🔍", "desc": "Gathering information"},
    {"name": "Analyzing", "icon": "🔬", "desc": "Extracting insights"},
    {"name": "Summarizing", "icon": "📝", "desc": "Generating summary"},
    {"name": "Reporting", "icon": "📄", "desc": "Creating report"},
    {"name": "Saving", "icon": "💾", "desc": "Storing to memory"},
]


def render_progress(current_step: int = 0, is_complete: bool = False) -> None:
    """
    Render the pipeline progress tracker.

    Parameters
    ----------
    current_step : int
        Current step index (0-based). -1 means not started.
    is_complete : bool
        Whether the pipeline has completed.
    """
    total = len(PIPELINE_STEPS)

    if is_complete:
        progress = 1.0
    elif current_step < 0:
        progress = 0.0
    else:
        progress = min((current_step + 1) / total, 1.0)

    st.progress(progress)

    cols = st.columns(total)

    for i, step in enumerate(PIPELINE_STEPS):
        with cols[i]:
            if is_complete or (current_step >= 0 and i < current_step):
                # Completed
                st.markdown(
                    f"""<div style="text-align:center;">
                        <div style="font-size:1.5rem;">✅</div>
                        <div style="font-size:0.7rem; color:#4ade80; font-weight:600;">
                            {step['name']}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            elif current_step >= 0 and i == current_step:
                # Active
                st.markdown(
                    f"""<div style="text-align:center;">
                        <div style="font-size:1.5rem; animation: pulse 1.5s infinite;">
                            {step['icon']}
                        </div>
                        <div style="font-size:0.7rem; color:#60a5fa; font-weight:600;">
                            {step['name']}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                # Pending
                st.markdown(
                    f"""<div style="text-align:center;">
                        <div style="font-size:1.5rem; opacity:0.3;">
                            {step['icon']}
                        </div>
                        <div style="font-size:0.7rem; color:#666;">
                            {step['name']}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
