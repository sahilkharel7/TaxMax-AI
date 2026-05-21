"""Shared pytest fixtures for the TaxMax backend.

These fixtures keep the existing deterministic test suite stable now that the
chat service can also call OpenAI. The QA tests in ``test_chat_endpoint.py``
and ``test_health.py`` were written against the safety-reviewed placeholder
responses, so we ensure no OpenAI key leaks in from the developer's local
``backend/.env`` while running the suite.

Tests that intentionally exercise the OpenAI path should set the key via
``monkeypatch.setenv("OPENAI_API_KEY", ...)`` and clear the settings cache.
"""

from __future__ import annotations

from typing import Iterator

import pytest

from app.config import get_settings
from app.services import chat_service


@pytest.fixture(autouse=True)
def _isolate_chat_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Force chat tests to use the deterministic fallback by default.

    Removes any ambient ``OPENAI_API_KEY`` (from ``backend/.env`` or the user's
    shell), resets the cached ``Settings`` instance so config changes take
    effect, and clears the in-memory chat session store between tests.
    """

    # NOTE: pydantic-settings reads OPENAI_API_KEY from backend/.env when the
    # environment variable is absent. Setting it to "" (rather than deleting
    # it) ensures the empty value wins over the .env entry, since environment
    # variables take precedence over the dotenv file.
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()
    chat_service.reset_all_sessions()
    yield
    get_settings.cache_clear()
    chat_service.reset_all_sessions()
