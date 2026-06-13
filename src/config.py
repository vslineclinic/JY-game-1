from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "공략노트 AI"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NOTES_FILE = DATA_DIR / "strategy_notes.json"
YOUTUBE_CACHE_FILE = DATA_DIR / "youtube_cache.json"
AI_CACHE_FILE = DATA_DIR / "ai_cache.json"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _get_from_streamlit_secrets(key: str) -> str | None:
    """Read from st.secrets only when Streamlit is available.

    Importing this module in tests or scripts should not require Streamlit runtime.
    """
    try:
        import streamlit as st  # type: ignore

        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else None
    except Exception:
        return None
    return None


def get_secret(key: str, default: str | None = None) -> str | None:
    """Return a secret from Streamlit secrets first, then environment variables."""
    return _get_from_streamlit_secrets(key) or os.getenv(key) or default


def get_openai_api_key() -> str | None:
    return get_secret("OPENAI_API_KEY")


def get_openai_model() -> str:
    return get_secret("OPENAI_MODEL", DEFAULT_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL


def get_youtube_api_key() -> str | None:
    return get_secret("YOUTUBE_API_KEY")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
