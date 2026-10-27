"""Investigation report generation (Markdown + CSV)."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from services.evidence_engine import Finding


def findings_to_csv(findings: list[Finding]) -> str:
    rows = [f.to_dict() for f in findings]
    if not rows:
        return ""
    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def build_markdown_report(
    title: str,
    dataset_name: str,
    profile_summary: str,
    findings: list[Finding],
    anomaly_summary: str,
    ai_answer: str | None = None,
    settings_text: str = "",
) -> str:
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Dataset:** {dataset_name}")
    lines.append(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}")
    lines.append("")
    lines.append("## Dataset summary")
    lines.append("```")
    lines.append(profile_summary)
    lines.append("```")
    lines.append("")
    lines.append("## Findings")
    if findings:
        for f in findings:
            lines.append(f"### {f.finding_id}: {f.title}")
            lines.append(f"- Type: {f.finding_type}")
            lines.append(f"- Summary: {f.summary}")
            lines.append(f"- Metric: {f.metric}")
            lines.append(f"- Columns: {', '.join(f.columns) if f.columns else 'n/a'}")
            lines.append(f"- Row refs: {f.row_refs[:20]}")
            lines.append(f"- Method: {f.method}")
            lines.append(f"- Confidence: {f.confidence}")
            lines.append(f"- Limitations: {f.limitations}")
            lines.append("")
    else:
        lines.append("No findings generated.")
    lines.append("")
    lines.append("## Anomalies")
    lines.append(anomaly_summary if anomaly_summary else "None detected.")
    lines.append("")
    if ai_answer:
        lines.append("## AI explanation (labeled)")
        lines.append("> AI-generated interpretation. Verify against evidence above.")
        lines.append("")
        lines.append(ai_answer)
        lines.append("")
    lines.append("## Limitations")
    lines.append("- Row references are tied to the current dataset version.")
    lines.append("- Statistics are computed on the uploaded data only; no external verification.")
    lines.append("- Anomalies are unusual observations, not proof of error or fraud.")
    lines.append("")
    lines.append("## Reproducibility notes")
    lines.append(settings_text or "Default settings.")
    lines.append("")
    return "\n".join(lines)