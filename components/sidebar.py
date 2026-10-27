"""Sidebar navigation component."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> str:
    st.sidebar.title("AEGIS X")
    st.sidebar.caption("Verify the data. Investigate the evidence. Understand the results.")
    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Data Profile", "Visualizations", "Anomalies", "Investigation", "Report"],
        index=0,
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("**AI status**")
    from config.settings import ai_configured
    if ai_configured():
        st.sidebar.success("AI configured")
    else:
        st.sidebar.warning("AI not configured")
    return page