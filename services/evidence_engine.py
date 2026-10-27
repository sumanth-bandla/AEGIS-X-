"""Evidence and provenance engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd


@dataclass
class Finding:
    finding_id: str
    title: str
    finding_type: str
    summary: str
    metric: str
    columns: list[str] = field(default_factory=list)
    row_refs: list[int] = field(default_factory=list)
    method: str = ""
    confidence: str = ""
    limitations: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "finding_type": self.finding_type,
            "summary": self.summary,
            "metric": self.metric,
            "columns": self.columns,
            "row_refs": self.row_refs,
            "method": self.method,
            "confidence": self.confidence,
            "limitations": self.limitations,
            "timestamp": self.timestamp,
        }


class EvidenceEngine:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def by_id(self, fid: str) -> Finding | None:
        for f in self.findings:
            if f.finding_id == fid:
                return f
        return None

    def to_dataframe(self) -> pd.DataFrame:
        if not self.findings:
            return pd.DataFrame()
        return pd.DataFrame([f.to_dict() for f in self.findings])

    def clear(self) -> None:
        self.findings = []

    def validate_ids(self, ids: list[str]) -> list[str]:
        existing = {f.finding_id for f in self.findings}
        return [i for i in ids if i in existing]


def anomaly_to_findings(anomalies: list[Any], df: pd.DataFrame) -> list[Finding]:
    out = []
    for a in anomalies:
        d = a.to_dict() if hasattr(a, "to_dict") else a
        fid = d["finding_id"]
        col = d["column"]
        row = d["row_index"]
        obs = d["observed_value"]
        out.append(
            Finding(
                finding_id=fid,
                title=f"Unusual value in {col}",
                finding_type="anomaly",
                summary=d["explanation"],
                metric=f"observed={obs}; {d['comparison']}",
                columns=[c for c in col.split(", ") if c and c != "(all columns)"],
                row_refs=[int(row) + 1],
                method=d["method"],
                confidence="Medium - statistical deviation from observed distribution",
                limitations="Statistical unusualness is not proof of error or fraud; small samples and skewed distributions can create false positives.",
            )
        )
    return out


def profile_to_findings(prof: Any) -> list[Finding]:
    out = []
    # missingness per column
    for c in prof.columns:
        if c.missing_count > 0:
            out.append(
                Finding(
                    finding_id=f"MISS-{c.name}",
                    title=f"Missing values in {c.name}",
                    finding_type="data_quality",
                    summary=f"Column '{c.name}' contains {c.missing_count} missing values ({c.missing_pct*100:.1f}%).",
                    metric=f"missing_count={c.missing_count}, missing_pct={c.missing_pct:.4f}",
                    columns=[c.name],
                    row_refs=[],
                    method="Missingness count",
                    confidence="High - direct count from dataset",
                    limitations="Missingness may be intentional or structural; zeros and empty strings are distinguished from NaN.",
                )
            )
    if prof.duplicate_row_count > 0:
        out.append(
            Finding(
                finding_id="DUP-ROWS",
                title="Duplicate rows",
                finding_type="data_quality",
                summary=f"{prof.duplicate_row_count} exact duplicate rows detected.",
                metric=f"duplicate_row_count={prof.duplicate_row_count}",
                columns=[],
                row_refs=[],
                method="Exact row duplication",
                confidence="High - direct comparison",
                limitations="Duplicates may be legitimate repeated records.",
            )
        )
    return out