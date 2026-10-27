"""Plotly figure builders for EDA."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def histogram(df: pd.DataFrame, column: str, bins: int = 30) -> go.Figure:
    fig = px.histogram(df, x=column, nbins=bins, title=f"Distribution of {column}")
    fig.update_layout(template="plotly_dark")
    return fig


def bar_chart(df: pd.DataFrame, column: str, top_n: int = 20) -> go.Figure:
    vc = df[column].value_counts(dropna=False).head(top_n)
    fig = px.bar(x=vc.index.astype(str), y=vc.values, labels={"x": column, "y": "count"},
                 title=f"Frequency of {column}")
    fig.update_layout(template="plotly_dark")
    return fig


def scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None) -> go.Figure:
    fig = px.scatter(df, x=x, y=y, color=color, title=f"{y} vs {x}")
    fig.update_layout(template="plotly_dark")
    return fig


def box_plot(df: pd.DataFrame, column: str, by: str | None = None) -> go.Figure:
    if by:
        fig = px.box(df, x=by, y=column, title=f"{column} by {by}")
    else:
        fig = px.box(df, y=column, title=f"Box plot of {column}")
    fig.update_layout(template="plotly_dark")
    return fig


def correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    import pandas as pd

    num = df.select_dtypes(include=[np.number])
    if num.shape[1] < 2:
        fig = go.Figure()
        fig.update_layout(title="Not enough numeric columns", template="plotly_dark")
        return fig
    corr = num.corr()
    fig = px.imshow(corr, text_auto=True, title="Correlation heatmap", aspect="auto")
    fig.update_layout(template="plotly_dark")
    return fig


def time_series(df: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    d = df[[date_col, value_col]].copy()
    try:
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    except Exception:  # noqa: BLE001
        pass
    d = d.sort_values(date_col)
    fig = px.line(d, x=date_col, y=value_col, title=f"{value_col} over time")
    fig.update_layout(template="plotly_dark")
    return fig