"""Dataset profiling: structural, missingness, numeric, categorical, datetime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from utils.formatting import fmt_bytes


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    missing_count: int
    missing_pct: float
    unique_count: int
    is_numeric: bool = False
    is_categorical: bool = False
    is_datetime: bool = False
    numeric_summary: dict[str, Any] = field(default_factory=dict)
    top_values: list[tuple[Any, int]] = field(default_factory=list)
    min_value: Any = None
    max_value: Any = None


@dataclass
class DatasetProfile:
    row_count: int
    column_count: int
    memory_bytes: int
    duplicate_row_count: int
    total_missing: int
    total_cells: int
    columns: list[ColumnProfile] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    datetime_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "memory_bytes": self.memory_bytes,
            "duplicate_row_count": self.duplicate_row_count,
            "total_missing": self.total_missing,
            "total_cells": self.total_cells,
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "quality_issues": self.quality_issues,
            "columns": [c.__dict__ for c in self.columns],
        }


def _is_datetime_series(s: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(s):
        return True
    if s.dtype == object:
        sample = s.dropna().astype(str).head(50)
        if len(sample) == 0:
            return False
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            return parsed.notna().mean() >= 0.8
        except Exception:  # noqa: BLE001
            return False
    return False


def _is_numeric_series(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)


def _is_categorical(s: pd.Series, n_rows: int) -> bool:
    if _is_numeric_series(s) or _is_datetime_series(s):
        return False
    # treat object/low-cardinality as categorical
    n_unique = s.nunique(dropna=True)
    if n_rows == 0:
        return False
    return n_unique <= max(50, int(0.2 * n_rows)) or s.dtype == object


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    prof = DatasetProfile(
        row_count=int(df.shape[0]),
        column_count=int(df.shape[1]),
        memory_bytes=int(df.memory_usage(deep=True).sum()),
        duplicate_row_count=int(df.duplicated().sum()),
        total_missing=int(df.isna().sum().sum()),
        total_cells=int(df.shape[0] * df.shape[1]) if df.shape[1] else 0,
    )

    for col in df.columns:
        s = df[col]
        cp = ColumnProfile(
            name=str(col),
            dtype=str(s.dtype),
            missing_count=int(s.isna().sum()),
            missing_pct=float(s.isna().mean()) if len(s) else 0.0,
            unique_count=int(s.nunique(dropna=True)),
        )
        if _is_datetime_series(s):
            cp.is_datetime = True
            prof.datetime_columns.append(str(col))
            try:
                dt = pd.to_datetime(s, errors="coerce")
                cp.min_value = dt.min()
                cp.max_value = dt.max()
            except Exception:  # noqa: BLE001
                pass
        elif _is_numeric_series(s):
            cp.is_numeric = True
            prof.numeric_columns.append(str(col))
            desc = s.describe()
            cp.numeric_summary = {
                "count": float(desc.get("count", 0)),
                "mean": float(desc.get("mean", float("nan"))),
                "std": float(desc.get("std", float("nan"))),
                "min": float(desc.get("min", float("nan"))),
                "25%": float(desc.get("25%", float("nan"))),
                "50%": float(desc.get("50%", float("nan"))),
                "75%": float(desc.get("75%", float("nan"))),
                "max": float(desc.get("max", float("nan"))),
            }
            cp.min_value = cp.numeric_summary["min"]
            cp.max_value = cp.numeric_summary["max"]
        else:
            if _is_categorical(s, prof.row_count):
                cp.is_categorical = True
                prof.categorical_columns.append(str(col))
            # top values
            vc = s.value_counts(dropna=False).head(10)
            cp.top_values = [(idx, int(cnt)) for idx, cnt in vc.items()]
            if len(s.dropna()) > 0:
                cp.min_value = None
                cp.max_value = None

        prof.columns.append(cp)

    # Quality issues
    issues = []
    if prof.total_missing > 0:
        pct = prof.total_missing / prof.total_cells * 100 if prof.total_cells else 0
        issues.append(f"{prof.total_missing} missing values ({pct:.1f}% of cells).")
    if prof.duplicate_row_count > 0:
        issues.append(f"{prof.duplicate_row_count} duplicate rows detected.")
    for cp in prof.columns:
        if cp.missing_pct > 0.5:
            issues.append(f"Column '{cp.name}' is more than 50% missing.")
        if cp.unique_count == 1 and prof.row_count > 1:
            issues.append(f"Column '{cp.name}' has a single unique value (constant).")
        if cp.is_numeric and cp.numeric_summary.get("std", 0) == 0:
            issues.append(f"Numeric column '{cp.name}' has zero variance.")
    if prof.row_count < 10:
        issues.append("Dataset has fewer than 10 rows; statistical results may be unreliable.")
    prof.quality_issues = issues
    return prof


def profile_to_dataframe(prof: DatasetProfile) -> pd.DataFrame:
    rows = []
    for c in prof.columns:
        rows.append(
            {
                "column": c.name,
                "dtype": c.dtype,
                "missing": c.missing_count,
                "missing_pct": round(c.missing_pct * 100, 2),
                "unique": c.unique_count,
                "type": "numeric"
                if c.is_numeric
                else "datetime"
                if c.is_datetime
                else "categorical"
                if c.is_categorical
                else "other",
            }
        )
    return pd.DataFrame(rows)