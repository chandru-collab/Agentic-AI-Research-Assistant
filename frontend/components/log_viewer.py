"""
Execution Log Viewer Component.

Displays the execution logs from the research pipeline
in a styled, expandable format.
"""

from __future__ import annotations

import streamlit as st


def render_logs(logs: list[str]) -> None:
    """
    Render execution logs in an expandable section.

    Parameters
    ----------
    logs : list[str]
        List of log messages from the pipeline.
    """
    if not logs:
        return

    with st.expander(f"📃 Execution Logs ({len(logs)} entries)", expanded=False):
        for log_entry in logs:
            # Color-code based on emoji/content
            if "❌" in log_entry:
                st.markdown(
                    f'<div style="color:#f87171; font-family:monospace; '
                    f'font-size:0.8rem; padding:4px 0; border-bottom: 1px solid #333;">'
                    f'{log_entry}</div>',
                    unsafe_allow_html=True,
                )
            elif "⚠️" in log_entry:
                st.markdown(
                    f'<div style="color:#fbbf24; font-family:monospace; '
                    f'font-size:0.8rem; padding:4px 0; border-bottom: 1px solid #333;">'
                    f'{log_entry}</div>',
                    unsafe_allow_html=True,
                )
            elif "🚀" in log_entry:
                st.markdown(
                    f'<div style="color:#60a5fa; font-family:monospace; '
                    f'font-size:0.8rem; padding:4px 0; border-bottom: 1px solid #333;">'
                    f'{log_entry}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="color:#4ade80; font-family:monospace; '
                    f'font-size:0.8rem; padding:4px 0; border-bottom: 1px solid #333;">'
                    f'{log_entry}</div>',
                    unsafe_allow_html=True,
                )
