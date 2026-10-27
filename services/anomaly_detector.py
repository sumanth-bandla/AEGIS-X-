"""Interpretable baseline anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from config.settings import SETTINGS


@dataclass
class AnomalyFinding:
    finding_id: str
    method: str
    column: str
    row_index: int  # 0-based position in dataframe
    observed_value: Any
    comparison: str
    threshold: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "method": self.method,
            "column": self.column,
            "row_index": self.row_index,
            "row_number": self.row_index + 1,
            "observed_value": self.observed_value,
            "comparison": self.comparison,
            "threshold": self.threshold,
            "explanation": self.explanation,
        }


def _next_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"ANOM-{counter[0]:03d}"


def detect_iqr_outliers(df: pd.DataFrame, column: str, multiplier: float | None = None) -> list[AnomalyFinding]:
    mult = multiplier if multiplier is not None else SETTINGS.iqr_multiplier
    s = df[column]
    if not pd.api.types.is_numeric_dtype(s):
        return []
    clean = s.dropna()
    if len(clean) < 5:
        return []
    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        return []
    lower = q1 - mult * iqr
    upper = q3 + mult * iqr
    findings: list[AnomalyFinding] = []
    counter = [0]
    # reuse global-ish; ids assigned later? We'll assign here with local counter starting 0; caller may renumber? Keep simple.
    for idx, val in s.items():
        if pd.isna(val):
            continue
        v = float(val)
        if v < lower or v > upper:
            side = "below lower bound" if v < lower else "above upper bound"
            findings.append(
                AnomalyFinding(
                    finding_id="",  # placeholder
                    method="IQR (interquartile range)",
                    column=column,
                    row_index=int(idx) if not isinstance(idx, (int, np.integer)) else int(idx),
                    observed_value=val,
                    comparison=f"Q1={q1:.4g}, Q3={q3:.4g}, IQR={iqr:.4g}",
                    threshold=f"{mult} x IQR (bounds [{lower:.4g}, {upper:.4g}])",
                    explanation=f"Value {val} is {side} of the IQR-based bounds.",
                )
            )
    # assign ids
    for f in findings:
        f.finding_id = _next_id(counter)
    # Note: counter resets per column; ids may collide across columns. Fix below by global counter passed? We'll renumber in detect_all.
    return findings


def detect_zscore_outliers(df: pd.DataFrame, column: str, threshold: float | None = None) -> list[AnomalyFinding]:
    thr = threshold if threshold is not None else SETTINGS.zscore_threshold
    s = df[column]
    if not pd.api.types.is_numeric_dtype(s):
        return []
    clean = s.dropna()
    if len(clean) < 8:
        return []
    mean = float(clean.mean())
    std = float(clean.std(ddof=0))
    if std == 0 or np.isnan(std):
        return []
    findings = []
    counter = [0]
    for idx, val in s.items():
        if pd.isna(val):
            continue
        z = (float(val) - mean) / std
        if abs(z) > thr:
            findings.append(
                AnomalyFinding(
                    finding_id="",
                    method="Z-score",
                    column=column,
                    row_index=int(idx),
                    observed_value=val,
                    comparison=f"mean={mean:.4g}, std={std:.4g}, z={z:.2f}",
                    threshold=f"|z| > {thr}",
                    explanation=f"Value {val} has z-score {z:.2f}, exceeding threshold {thr}.",
                )
            )
    for f in findings:
        f.finding_id = _next_id(counter)
    return findings


def detect_missingness(df: pd.DataFrame) -> list[AnomalyFinding]:
    findings = []
    counter = [0]
    # rows with any missing
    missing_mask = df.isna().any(axis=1)
    for idx in df.index[missing_mask]:
        missing_cols = [c for c in df.columns if pd.isna(df.loc[idx, c])]
        findings.append(
            AnomalyFinding(
                finding_id="",
                method="Missingness rule",
                column=", ".join(missing_cols),
                row_index=int(idx),
                observed_value=None,
                comparison="NA/empty cell",
                threshold="any missing value",
                explanation=f"Row has missing values in columns: {', '.join(missing_cols)}.",
            )
        )
    for f in findings:
        f.finding_id = _next_id(counter)
    return findings


def detect_duplicates(df: pd.DataFrame) -> list[AnomalyFinding]:
    findings = []
    counter = [0]
    dup_mask = df.duplicated(keep="first")
    for idx in df.index[dup_mask]:
        findings.append(
            AnomalyFinding(
                finding_id="",
                method="Duplicate row rule",
                column="(all columns)",
                row_index=int(idx),
                observed_value=None,
                comparison="identical to an earlier row",
                threshold="exact duplicate",
                explanation="Row is an exact duplicate of a previous row.",
            )
        )
    for f in findings:
        f.finding_id = _next_id(counter)
    return findings


def detect_all(df: pd.DataFrame, numeric_columns: list[str] | None = None) -> list[AnomalyFinding]:
    if numeric_columns is None:
        numeric_columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    all_findings: list[AnomalyFinding] = []
    # IQR + zscore per numeric column
    for col in numeric_columns:
        all_findings.extend(detect_iqr_outliers(df, col))
        all_findings.extend(detect_zscore_outliers(df, col))
    all_findings.extend(detect_missingness(df))
    all_findings.extend(detect_duplicates(df))
    # renumber globally
    for i, f in enumerate(all_findings, start=1):
        f.finding_id = f"ANOM-{i:03d}"
    return all_findings