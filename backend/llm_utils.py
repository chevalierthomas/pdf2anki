"""Shared helpers for working with the OpenAI async client."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:  # pragma: no cover - optional dependency during tests
    from openai import AsyncOpenAI
    from openai import OpenAIError
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore
    OpenAIError = Exception  # type: ignore


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EXTRACTION_MODEL = os.getenv("OPENAI_EXTRACTION_MODEL", DEFAULT_MODEL)
REFINEMENT_MODEL = os.getenv("OPENAI_REFINEMENT_MODEL", DEFAULT_MODEL)


@lru_cache(maxsize=1)
def _client_factory() -> Optional[AsyncOpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or AsyncOpenAI is None:
        return None
    return AsyncOpenAI(api_key=api_key)


def get_async_client() -> Optional[AsyncOpenAI]:
    """Return a cached AsyncOpenAI client when credentials are configured."""

    return _client_factory()


def estimate_tokens(text: str) -> int:
    """Very rough heuristic to estimate token usage for chunking."""

    # Average English token ≈ 4 characters; clamp to positive integers.
    return max(1, len(text) // 4)


__all__ = [
    "AsyncOpenAI",
    "OpenAIError",
    "DEFAULT_MODEL",
    "EXTRACTION_MODEL",
    "REFINEMENT_MODEL",
    "get_async_client",
    "estimate_tokens",
]

