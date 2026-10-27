"""Formatting helpers for display values."""

from __future__ import annotations

from typing import Any


def fmt_number(value: Any, decimals: int = 2) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(v) >= 1_000_000:
        return f"{v:,.0f}"
    if abs(v) >= 1000:
        return f"{v:,.2f}"
    return f"{v:.{decimals}f}"


def fmt_percent(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"