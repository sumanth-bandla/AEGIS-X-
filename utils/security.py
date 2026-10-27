"""Security helpers: sanitization, safe rendering, secret hygiene."""

from __future__ import annotations

import html
import re
from typing import Any


def sanitize_text(value: Any) -> str:
    """Coerce to string and strip HTML-ish content for safe display."""
    if value is None:
        return ""
    text = str(value)
    # Remove control characters
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return text


def escape_for_markdown(value: Any) -> str:
    text = sanitize_text(value)
    # Escape markdown special that could break tables
    return text.replace("|", "\\|").replace("\n", " ")


def redact_secrets(text: str) -> str:
    """Best-effort redaction of obvious secret-like tokens in logs/errors."""
    patterns = [
        r"sk-[A-Za-z0-9_\-]{10,}",
        r"nvapi-[A-Za-z0-9_\-]{10,}",
    ]
    for p in patterns:
        text = re.sub(p, "[REDACTED]", text)
    return text


def safe_error_message(exc: Exception) -> str:
    return redact_secrets(str(exc))[:300]