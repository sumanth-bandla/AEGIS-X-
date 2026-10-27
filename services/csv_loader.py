"""CSV loading, validation, and normalization."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from config.settings import SETTINGS
from utils.security import safe_error_message
from utils.validation import (
    detect_duplicate_columns,
    is_valid_csv_bytes,
    normalize_column_names,
)


@dataclass
class LoadResult:
    df: pd.DataFrame | None = None
    original_columns: list[str] = field(default_factory=list)
    normalized_columns: list[str] = field(default_factory=list)
    column_map: dict[str, str] = field(default_factory=dict)
    duplicate_columns: list[str] = field(default_factory=list)
    encoding_used: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.df is not None and not self.errors


def load_csv(uploaded_file: Any) -> LoadResult:
    result = LoadResult()
    try:
        raw = uploaded_file.read() if hasattr(uploaded_file, "read") else uploaded_file
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"Could not read file: {safe_error_message(exc)}")
        return result

    if not isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.encode("utf-8")
        except Exception:  # noqa: BLE001
            result.errors.append("Uploaded file is not readable as bytes.")
            return result

    if len(raw) == 0:
        result.errors.append("The uploaded file is empty.")
        return result

    if len(raw) > SETTINGS.max_upload_bytes:
        result.errors.append(
            f"File size {len(raw)} bytes exceeds limit of {SETTINGS.max_upload_bytes} bytes."
        )
        return result

    if not is_valid_csv_bytes(raw):
        result.errors.append("File does not look like a valid CSV.")
        return result

    # Try encodings
    df = None
    encoding_used = None
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            encoding_used = enc
            break
        except UnicodeDecodeError:
            continue
        except Exception as exc:  # noqa: BLE001
            # try next
            last_err = exc
            continue
    if df is None:
        # last attempt with default
        try:
            df = pd.read_csv(io.BytesIO(raw))
            encoding_used = "default"
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Could not parse CSV: {safe_error_message(exc)}")
            return result

    # Resource limits
    if df.shape[0] > SETTINGS.max_rows:
        result.errors.append(
            f"Row count {df.shape[0]} exceeds limit of {SETTINGS.max_rows}."
        )
        return result
    if df.shape[1] > SETTINGS.max_columns:
        result.errors.append(
            f"Column count {df.shape[1]} exceeds limit of {SETTINGS.max_columns}."
        )
        return result
    if df.shape[0] == 0:
        result.errors.append("CSV contains no data rows.")
        return result

    # Recover original header names (pandas mangles duplicate names)
    header_names = None
    try:
        text = raw.decode(encoding_used or "utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        header_names = next(reader, None)
    except Exception:  # noqa: BLE001
        header_names = None
    if header_names and len(header_names) == df.shape[1]:
        original_columns = [str(c) for c in header_names]
    else:
        original_columns = [str(c) for c in df.columns.tolist()]
    result.duplicate_columns = detect_duplicate_columns(original_columns)

    normalized, mapping = normalize_column_names(original_columns)
    df.columns = normalized

    result.df = df
    result.original_columns = original_columns
    result.normalized_columns = normalized
    result.column_map = mapping
    result.encoding_used = encoding_used

    # Warnings
    if result.duplicate_columns:
        result.warnings.append(
            f"Duplicate column names detected (case-insensitive): {result.duplicate_columns}"
        )
    missing_total = int(df.isna().sum().sum())
    if missing_total > 0:
        result.warnings.append(f"Dataset contains {missing_total} missing values.")

    return result