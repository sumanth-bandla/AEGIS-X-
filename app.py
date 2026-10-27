"""AEGIS X - Open AI Investigation Agent (Streamlit entrypoint)."""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from components.evidence_panel import render_findings
from components.sidebar import render_sidebar
from config.settings import SETTINGS, ai_configured
from services.analytics import column_summary, group_comparison, top_correlations
from services.anomaly_detector import detect_anomalies
from services.csv_loader import load_csv
from services.data_profiler import profile_dataset
from services.evidence_engine import build_anomaly_findings, build_findings_from_profile
from services.investigation_service import ask, build_context
from services.report_generator import build_markdown_report, findings_to_csv
from utils.formatting import fmt_bytes, fmt_number
from utils.security import sanitize_text

st.set_page_config(page_title="AEGIS X", page_icon="🛡️", layout="wide")

# Dark theme via CSS
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e6e6e6; }
    .metric-card { background: #161b22; border: 1px solid #2a3441; border-radius: 8px; padding: 12px; }
    h1, h2, h3 { color: #7dd3fc; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state init
for key in ["df", "profile", "load_result", "findings", "anomaly_report", "ai_result"]:
    if key not in st.session_state:
        st.session_state[key] = None

page = render_sidebar()

# Header
st.title("AEGIS X — Open AI Investigation Agent")
st.caption("Verify the data. Investigate the evidence. Understand the results.")

# Upload area (always available)
with st.expander("Dataset upload", expanded=st.session_state.df is None):
    uploaded = st.file_uploader("Upload CSV", type=["csv"], help=f"Max {SETTINGS.max_upload_bytes // (1024*1024)} MB")
    if uploaded is not None:
        if st.button("Load dataset"):
            with st.spinner("Loading and validating..."):
                lr = load_csv(uploaded)
                st.session_state.load_result = lr
                if lr.ok:
                    st.session_state.df = lr.df
                    st.session_state.profile = profile_dataset(lr.df)
                    st.session_state.findings = build_findings_from_profile(st.session_state.profile, lr.df)
                    ar = detect_anomalies(lr.df)
                    st.session_state.anomaly_report = ar
                    st.session_state.findings = st.session_state.findings + build_anomaly_findings(ar, lr.df)
                    st.success(f"Loaded {lr.df.shape[0]} rows x {lr.df.shape[1]} columns.")
                else:
                    for e in lr.errors:
                        st.error(e)
                for w in (lr.warnings or []):
                    st.warning(w)

df: pd.DataFrame | None = st.session_state.df

if df is None:
    st.info("Upload a CSV to begin. The app works fully without an AI API key for profiling, charts, and statistics.")
    st.stop()

profile = st.session_state.profile

# ---------------- Overview ----------------
if page == "Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{profile.row_count:,}")
    c2.metric("Columns", profile.column_count)
    c3.metric("Missing values", int(df.isna().sum().sum()))
    c4.metric("Duplicate rows", profile.duplicate_rows)
    st.write(f"Memory: {fmt_bytes(profile.memory_bytes)}")
    st.subheader("Columns")
    col_df = pd.DataFrame(
        [
            {
                "column": c.name,
                "dtype": c.dtype,
                "inferred": c.inferred,
                "missing": c.missing_count,
                "missing_pct": round(c.missing_pct * 100, 1),
                "unique": c.unique_count,
            }
            for c in profile.columns
        ]
    )
    st.dataframe(col_df, use_container_width=True)
    if profile.quality_issues:
        st.subheader("Data quality issues")
        for q in profile.quality_issues:
            st.warning(q)

# ---------------- Data Profile ----------------
elif page == "Data Profile":
    st.subheader("Numeric summary")
    if profile.numeric_summary is not None and not profile.numeric_summary.empty:
        st.dataframe(profile.numeric_summary, use_container_width=True)
    else:
        st.info("No numeric columns.")
    st.subheader("Categorical distributions")
    if profile.categorical_summary:
        for col, vc in profile.categorical_summary.items():
            st.write(f"**{col}**")
            st.bar_chart(vc)
    else:
        st.info("No categorical columns.")
    st.subheader("Date columns")
    st.write(profile.date_columns if profile.date_columns else "None detected.")
    st.subheader("Column detail")
    sel = st.selectbox("Select column", df.columns.tolist())
    st.json(column_summary(df, sel))

# ---------------- Visualizations ----------------
elif page == "Visualizations":
    from services.visualization import (
        bar_chart,
        box_plot,
        correlation_heatmap,
        histogram,
        scatter_plot,
        time_series,
    )

    chart_type = st.selectbox("Chart type", ["Histogram", "Bar", "Scatter", "Box", "Correlation heatmap", "Time series"])
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c.name for c in profile.columns if c.inferred in ("categorical", "boolean", "text")]

    if chart_type == "Histogram":
        c = st.selectbox("Column", df.columns.tolist())
        fig = histogram(df, c)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Bar":
        c = st.selectbox("Column", df.columns.tolist())
        fig = bar_chart(df, c)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Scatter":
        if len(numeric_cols) < 2:
            st.info("Need at least two numeric columns.")
        else:
            x = st.selectbox("X", numeric_cols)
            y = st.selectbox("Y", numeric_cols, index=min(1, len(numeric_cols) - 1))
            color = st.selectbox("Color (optional)", [None] + cat_cols)
            fig = scatter_plot(df, x, y, color)
            st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Box":
        c = st.selectbox("Numeric column", numeric_cols if numeric_cols else df.columns.tolist())
        by = st.selectbox("Group by (optional)", [None] + (cat_cols if cat_cols else []))
        fig = box_plot(df, c, by)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Correlation heatmap":
        if len(numeric_cols) < 2:
            st.info("Need at least two numeric columns.")
        else:
            fig = correlation_heatmap(df, numeric_cols)
            st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Time series":
        date_cols = profile.date_columns
        if not date_cols or not numeric_cols:
            st.info("Need a date column and a numeric column.")
        else:
            d = st.selectbox("Date column", date_cols)
            v = st.selectbox("Value column", numeric_cols)
            # ensure datetime
            tmp = df.copy()
            tmp[d] = pd.to_datetime(tmp[d], errors="coerce")
            fig = time_series(tmp, d, v)
            st.plotly_chart(fig, use_container_width=True)

# ---------------- Anomalies ----------------
elif page == "Anomalies":
    ar = st.session_state.anomaly_report
    st.write(f"Methods used: {', '.join(ar.methods_used) if ar.methods_used else 'none'}")
    for n in ar.notes:
        st.info(n)
    st.write(f"Total flagged records: {len(ar.anomalies)}")
    if ar.anomalies:
        rows = [
            {
                "column": a.column,
                "row_index": a.row_index,
                "value": a.value,
                "method": a.method,
                "rule": a.rule,
                "comparison": a.comparison,
                "severity": a.severity,
            }
            for a in ar.anomalies[:500]
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("Row indices are 0-based positions in the current dataset.")
        # inspect record
        idx = st.number_input("Inspect row index", min_value=0, max_value=len(df) - 1, value=0, step=1)
        st.dataframe(df.iloc[[int(idx)]], use_container_width=True)
    else:
        st.success("No anomalies detected by baseline methods.")

# ---------------- Investigation ----------------
elif page == "Investigation":
    st.subheader("Ask a question about this dataset")
    q = st.text_area("Question", placeholder="What are the most important patterns?")
    if st.button("Ask AEGIS X") and q.strip():
        with st.spinner("Analyzing..."):
            profile_summary = (
                f"rows={profile.row_count}, cols={profile.column_count}, missing={int(df.isna().sum().sum())}, "
                f"duplicate_rows={profile.duplicate_rows}, date_columns={profile.date_columns}"
            )
            anomaly_summary = f"methods={st.session_state.anomaly_report.methods_used}, flagged={len(st.session_state.anomaly_report.anomalies)}"
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

# ---------------- Report ----------------
elif page == "Report":
    st.subheader("Generate investigation report")
    title = st.text_input("Report title", value="AEGIS X Investigation Report")
    dataset_name = st.text_input("Dataset name", value="uploaded_dataset.csv")
    ai_answer = None
    if st.session_state.ai_result and st.session_state.ai_result.get("answer"):
        ai_answer = st.session_state.ai_result["answer"]
    if st.button("Build report"):
        profile_summary = (
            f"rows={profile.row_count}, cols={profile.column_count}, missing={int(df.isna().sum().sum())}, "
            f"duplicate_rows={profile.duplicate_rows}"
        )
        anomaly_summary = f"methods={st.session_state.anomaly_report.methods_used}, flagged={len(st.session_state.anomaly_report.anomalies)}"
        md = build_markdown_report(title, dataset_name, profile_summary, st.session_state.findings, anomaly_summary, ai_answer)
        st.session_state.report_md = md
        st.success("Report built.")
    if "report_md" in st.session_state and st.session_state.report_md:
        st.download_button("Download report (Markdown)", st.session_state.report_md, file_name="aegis_report.md", mime="text/markdown")
        csv = findings_to_csv(st.session_state.findings)
        if csv:
            st.download_button("Download findings (CSV)", csv, file_name="findings.csv", mime="text/csv")
        with st.expander("Preview"):
            st.markdown(st.session_state.report_md)