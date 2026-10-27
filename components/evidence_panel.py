"""Evidence panel rendering."""

from __future__ import annotations

import streamlit as st

from services.evidence_engine import Finding


def render_findings(findings: list[Finding]) -> None:
    if not findings:
        st.info("No findings generated yet.")
        return
    for f in findings:
        with st.expander(f"{f.finding_id}: {f.title}"):
            st.write(f"**Type:** {f.finding_type}")
            st.write(f"**Summary:** {f.summary}")
            st.write(f"**Metric:** {f.metric}")
            st.write(f"**Columns:** {', '.join(f.columns) if f.columns else 'n/a'}")
            st.write(f"**Row refs:** {f.row_refs[:20]}")
            st.write(f"**Method:** {f.method}")
            st.write(f"**Confidence:** {f.confidence}")
            st.write(f"**Limitations:** {f.limitations}")