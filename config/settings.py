"""Application configuration and resource limits for AEGIS X."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class Settings:
    app_name: str = "AEGIS X"
    tagline: str = "Verify the data. Investigate the evidence. Understand the results."

    # Upload / resource limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_rows: int = 200_000
    max_columns: int = 200
    preview_rows: int = 50

    # Anomaly detection
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0

    # AI
    ai_timeout_seconds: int = 30
    ai_max_context_chars: int = 12_000

    # Environment-driven (read at runtime via env)
    env_keys: tuple[str, ...] = field(default_factory=lambda: (
        "NEBIUS_API_KEY",
        "NEBIUS_BASE_URL",
        "NEBIUS_MODEL",
        "NVIDIA_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
    ))


# Sensible defaults for Nebius / NVIDIA open models
DEFAULT_NEBIUS_BASE_URL: Final[str] = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_MODEL: Final[str] = "nvidia/nemotron-3-super-120b-a12b"  # override via env


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def ai_configured() -> bool:
    key = get_env("NEBIUS_API_KEY") or get_env("OPENAI_API_KEY")
    return bool(key)


def get_ai_settings() -> dict:
    api_key = get_env("NEBIUS_API_KEY") or get_env("OPENAI_API_KEY")
    base_url = (
        get_env("NEBIUS_BASE_URL")
        or get_env("OPENAI_BASE_URL")
        or DEFAULT_NEBIUS_BASE_URL
    )
    model = (
        get_env("NEBIUS_MODEL")
        or get_env("NVIDIA_MODEL")
        or get_env("OPENAI_MODEL")
        or DEFAULT_MODEL
    )
    provider_label = (
        get_env("NEBIUS_PROVIDER_LABEL")
        or get_env("OPENAI_PROVIDER_LABEL")
        or "Nebius / NVIDIA"
    )
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "provider_label": provider_label,
        "timeout": get_env("AI_TIMEOUT", str(30)),
    }


SETTINGS = Settings()