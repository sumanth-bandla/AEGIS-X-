"""AEGIS X - Open AI Investigation Agent (Streamlit entrypoint)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.evidence_panel import render_findings
from components.sidebar import render_sidebar
from config.settings import SETTINGS, ai_configured
from services.analytics import (
    correlation_matrix,
    group_summary,
    missingness_summary,
    numeric_summary,
    top_correlations,
)
from services.anomaly_detector import detect_all
from services.csv_loader import load_csv
from services.data_profiler import profile_dataset, profile_to_dataframe
from services.evidence_engine import anomaly_to_findings, profile_to_findings
from services.investigation_service import ask
from services.report_generator import build_markdown_report, findings_to_csv
from services.visualization import (
    bar_chart,
    box_plot,
    correlation_heatmap,
    histogram,
    scatter,
    time_series,
)
from utils.formatting import fmt_bytes

st.set_page_config(page_title="AEGIS X", page_icon=" shield", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e6e6e6; }
    h1, h2, h3 { color: #7dd3fc; }
    </style>
    """,
    unsafe_allow_html=True,
)

for key in ["df", "profile", "load_result", "findings", "anomalies", "ai_result", "report_md"]:
    if key not in st.session_state:
        st.session_state[key] = None

page = render_sidebar()

st.title("AEGIS X — Open AI Investigation Agent")
st.caption("Verify the data. Investigate the evidence. Understand the results.")

with st.expander("Dataset upload", expanded=st.session_state.df is None):
    uploaded = st.file_uploader("Upload CSV", type=["csv"], help=f"Max {SETTINGS.max_upload_bytes // (1024*1024)} MB")
    if uploaded is not None:
        if st.button("Load dataset"):
            with st.spinner("Loading and validating..."):
                lr = load_csv(uploaded)
                st.session_state.load_result = lr
                if lr.ok:
                    st.session_state.df = lr.df
                    prof = profile_dataset(lr.df)
                    st.session_state.profile = prof
                    anoms = detect_all(lr.df)
                    st.session_state.anomalies = anoms
                    findings = profile_to_findings(prof) + anomaly_to_findings(anoms, lr.df)
                    st.session_state.findings = findings
                    st.success(f"Loaded {lr.df.shape[0]} rows x {lr.df.shape[1]} columns.")
                else:
                    for e in lr.errors:
                        st.error(e)
                for w in (lr.warnings or []):
                    st.warning(w)

df = st.session_state.df
if df is None:
    st.info("Upload a CSV to begin. The app works fully without an AI API key for profiling, charts, and statistics.")
    st.stop()

profile = st.session_state.profile
anomalies = st.session_state.anomalies or []

if page == "Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{profile.row_count:,}")
    c2.metric("Columns", profile.column_count)
    c3.metric("Missing values", profile.total_missing)
    c4.metric("Duplicate rows", profile.duplicate_row_count)
    st.write(f"Memory: {fmt_bytes(profile.memory_bytes)}")
    st.subheader("Columns")
    st.dataframe(profile_to_dataframe(profile), use_container_width=True)
    if profile.quality_issues:
        st.subheader("Data quality issues")
        for q in profile.quality_issues:
            st.warning(q)

elif page == "Data Profile":
    st.subheader("Numeric summary")
    ns = numeric_summary(df)
    if ns is not None and not ns.empty:
        st.dataframe(ns, use_container_width=True)
    else:
        st.info("No numeric columns.")
    st.subheader("Missingness")
    st.dataframe(missingness_summary(df), use_container_width=True)
    st.subheader("Top correlations")
    tc = top_correlations(df)
    if tc:
        st.dataframe(pd.DataFrame(tc), use_container_width=True)
    else:
        st.info("Not enough numeric columns.")
    st.subheader("Column detail")
    sel = st.selectbox("Select column", df.columns.tolist())
    colprof = next((c for c in profile.columns if c.name == sel), None)
    if colprof:
        st.json(colprof.__dict__)

elif page == "Visualizations":
    chart_type = st.selectbox("Chart type", ["Histogram", "Bar", "Scatter", "Box", "Correlation heatmap", "Time series"])
    numeric_cols = profile.numeric_columns
    cat_cols = profile.categorical_columns

    if chart_type == "Histogram":
        c = st.selectbox("Column", df.columns.tolist())
        st.plotly_chart(histogram(df, c), use_container_width=True)
    elif chart_type == "Bar":
        c = st.selectbox("Column", df.columns.tolist())
        st.plotly_chart(bar_chart(df, c), use_container_width=True)
    elif chart_type == "Scatter":
        if len(numeric_cols) < 2:
            st.info("Need at least two numeric columns.")
        else:
            x = st.selectbox("X", numeric_cols)
            y = st.selectbox("Y", numeric_cols, index=min(1, len(numeric_cols) - 1))
            color = st.selectbox("Color (optional)", [None] + (cat_cols if cat_cols else []))
            st.plotly_chart(scatter(df, x, y, color), use_container_width=True)
    elif chart_type == "Box":
        cols = numeric_cols if numeric_cols else df.columns.tolist()
        c = st.selectbox("Numeric column", cols)
        by = st.selectbox("Group by (optional)", [None] + (cat_cols if cat_cols else []))
        st.plotly_chart(box_plot(df, c, by), use_container_width=True)
    elif chart_type == "Correlation heatmap":
        if len(numeric_cols) < 2:
            st.info("Need at least two numeric columns.")
        else:
            st.plotly_chart(correlation_heatmap(df), use_container_width=True)
    elif chart_type == "Time series":
        date_cols = profile.datetime_columns
        if not date_cols or not numeric_cols:
            st.info("Need a date column and a numeric column.")
        else:
            d = st.selectbox("Date column", date_cols)
            v = st.selectbox("Value column", numeric_cols)
            tmp = df.copy()
            tmp[d] = pd.to_datetime(tmp[d], errors="coerce")
            st.plotly_chart(time_series(tmp, d, v), use_container_width=True)

elif page == "Anomalies":
    st.write(f"Total flagged records: {len(anomalies)}")
    if anomalies:
        rows = [a.to_dict() for a in anomalies]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("Row indices are 0-based positions in the current dataset.")
        idx = st.number_input("Inspect row index", min_value=0, max_value=len(df) - 1, value=0, step=1)
        st.dataframe(df.iloc[[int(idx)]], use_container_width=True)
    else:
        st.success("No anomalies detected by baseline methods.")

elif page == "Investigation":
    st.subheader("Ask a question about this dataset")
    q = st.text_area("Question", placeholder="What are the most important patterns?")
    if st.button("Ask AEGIS X") and q.strip():
        with st.spinner("Analyzing..."):
            profile_summary = (
                f"rows={profile.row_count}, cols={profile.column_count}, missing={profile.total_missing}, "
                f"duplicate_rows={profile.duplicate_row_count}, date_columns={profile.datetime_columns}, "
                f"numeric_columns={profile.numeric_columns}"
            )
            anomaly_summary = f"flagged={len(anomalies)}"
            result = ask(q, profile_summary, st.session_state.findings, anomaly_summary)
            st.session_state.ai_result = result

    res = st.session_state.ai_result
    if res:
        st.markdown(f"**Status:** {res.get('ai_status')}")
        st.markdown(f"### Answer\n{res.get('answer')}")
        if res.get("supporting_findings"):
            st.markdown(f"**Supporting findings:** {', '.join(res['supporting_findings'])}")
        if res.get("relevant_metrics"):
            st.markdown("**Relevant metrics:**")
            for m in res["relevant_metrics"]:
                st.write(f"- {m}")
        if res.get("limitations"):
            st.markdown(f"**Limitations:** {res['limitations']}")
        if res.get("error"):
            st.error(res["error"])

    st.subheader("Evidence")
    render_findings(st.session_state.findings)

elif page == "Report":
    st.subheader("Generate investigation report")
    title = st.text_input("Report title", value="AEGIS X Investigation Report")
    dataset_name = st.text_input("Dataset name", value="uploaded_dataset.csv")
    ai_answer = None
    if st.session_state.ai_result and st.session_state.ai_result.get("answer"):
        ai_answer = st.session_state.ai_result["answer"]
    if st.button("Build report"):
        profile_summary = (
            f"rows={profile.row_count}, cols={profile.column_count}, missing={profile.total_missing}, "
            f"duplicate_rows={profile.duplicate_row_count}"
        )
        anomaly_summary = f"flagged={len(anomalies)}"
        md = build_markdown_report(title, dataset_name, profile_summary, st.session_state.findings, anomaly_summary, ai_answer)
        st.session_state.report_md = md
        st.success("Report built.")
    if st.session_state.report_md:
        st.download_button("Download report (Markdown)", st.session_state.report_md, file_name="aegis_report.md", mime="text/markdown")
        csv = findings_to_csv(st.session_state.findings)
        if csv:
            st.download_button("Download findings (CSV)", csv, file_name="findings.csv", mime="text/csv")
        with st.expander("Preview"):
            st.markdown(st.session_state.report_md)