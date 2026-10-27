"""Deterministic analytics helpers: correlations, summaries, grouping."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not num_cols:
        return pd.DataFrame()
    return df[num_cols].describe().T


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        return pd.DataFrame()
    return df[num_cols].corr(numeric_only=True)


def top_correlations(df: pd.DataFrame, top_n: int = 10) -> list[dict[str, Any]]:
    corr = correlation_matrix(df)
    if corr.empty:
        return []
    pairs = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if pd.isna(val):
                continue
            pairs.append(
                {"column_a": cols[i], "column_b": cols[j], "correlation": float(val)}
            )
    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return pairs[:top_n]


def group_summary(df: pd.DataFrame, group_col: str, value_col: str, agg: str = "mean") -> pd.DataFrame:
    if group_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    g = df.groupby(group_col, dropna=False)[value_col].agg(agg)
    return g.reset_index().rename(columns={value_col: agg})


def missingness_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        rows.append(
            {
                "column": col,
                "missing_count": int(df[col].isna().sum()),
                "missing_pct": float(df[col].isna().mean()),
                "non_missing": int(df[col].notna().sum()),
            }
        )
    return pd.DataFrame(rows)