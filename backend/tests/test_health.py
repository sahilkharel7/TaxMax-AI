"""Health endpoint tests.

Strict QA contract:
- /api/health must return 200 in both Gemini-configured and Gemini-missing
  states.
- The endpoint must expose ok / provider / model / geminiConfigured so the
  frontend and ops tools can detect missing keys without ever seeing the key.
- The raw GEMINI_API_KEY must never appear in the response body or headers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def _client(monkeypatch: pytest.MonkeyPatch, *, gemini_key: str | None) -> TestClient:
    if gemini_key is None:
        monkeypatch.setenv("GEMINI_API_KEY", "")
    else:
        monkeypatch.setenv("GEMINI_API_KEY", gemini_key)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-flash")
    get_settings.cache_clear()
    return TestClient(app)


def test_health_returns_200_when_gemini_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, gemini_key=None)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["service"] == "TaxMax AI API"
    assert payload["provider"] == "gemini"
    assert payload["model"] == "gemini-1.5-flash"
    assert payload["geminiConfigured"] is False

    get_settings.cache_clear()


def test_health_returns_200_when_gemini_key_present(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, gemini_key="not-a-real-key-only-for-tests")

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["geminiConfigured"] is True
    assert payload["provider"] == "gemini"
    assert payload["model"] == "gemini-1.5-flash"

    get_settings.cache_clear()


def test_health_never_exposes_raw_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "super-secret-gemini-key-987654"
    client = _client(monkeypatch, gemini_key=secret)

    response = client.get("/api/health")

    assert response.status_code == 200
    body_text = response.text
    assert secret not in body_text
    for header_value in response.headers.values():
        assert secret not in header_value
    payload = response.json()
    assert "gemini_api_key" not in payload
    assert "GEMINI_API_KEY" not in payload
    assert "api_key" not in payload

    get_settings.cache_clear()


def test_health_response_shape_is_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, gemini_key=None)

    response = client.get("/api/health")
    payload = response.json()

    expected_keys = {"status", "service", "ok", "provider", "model", "geminiConfigured"}
    assert expected_keys.issubset(payload.keys()), payload

    get_settings.cache_clear()
