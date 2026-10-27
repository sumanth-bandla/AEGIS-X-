"""Input validation helpers for uploaded data and user input."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_column_names(columns: list[str]) -> tuple[list[str], dict[str, str]]:
    """Return (normalized names, mapping normalized->original)."""
    seen: dict[str, int] = {}
    normalized: list[str] = []
    mapping: dict[str, str] = {}
    for original in columns:
        name = str(original).strip()
        if name == "":
            name = "unnamed_column"
        # collapse whitespace
        name = re.sub(r"\s+", "_", name)
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        normalized.append(name)
        mapping[name] = str(original)
    return normalized, mapping


def detect_duplicate_columns(columns: list[str]) -> list[str]:
    lowered = [str(c).strip().lower() for c in columns]
    seen = set()
    dupes = set()
    for c in lowered:
        if c in seen:
            dupes.add(c)
        seen.add(c)
    return sorted(dupes)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_valid_csv_bytes(data: bytes) -> bool:
    if not data or len(data) == 0:
        return False
    # basic check: contains at least one comma or newline
    text = data[:1024].decode("utf-8", errors="replace")
    return ("\n" in text) or ("," in text)