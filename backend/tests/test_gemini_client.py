from types import SimpleNamespace

import httpx
import pytest

from app.config import get_settings
from app.services import gemini_client
from app.services.gemini_client import (
    GeminiNotConfiguredError,
    generate_structured_agent_response,
)


def test_missing_api_key_raises_controlled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(GeminiNotConfiguredError):
        generate_structured_agent_response(
            system_prompt="Return JSON.",
            user_payload={"redacted": True},
            response_schema_name="TaxAnalysisResponse",
        )

    get_settings.cache_clear()


def test_generate_structured_response_uses_configured_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()
    captured: dict[str, object] = {}

    class FakeModels:
        def generate_content(self, *, model: str, contents: str, config: object) -> object:
            captured["model"] = model
            captured["contents"] = contents
            captured["config"] = config
            return SimpleNamespace(text='{"status": "ok", "findings": []}')

    class FakeClient:
        def __init__(self, *, api_key: str, http_options: object) -> None:
            captured["api_key"] = api_key
            captured["http_options"] = http_options
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)

    response = generate_structured_agent_response(
        system_prompt="Return JSON.",
        user_payload={"wages": "redacted"},
        response_schema_name="TaxAnalysisResponse",
    )

    assert response == {"status": "ok", "findings": []}
    assert captured["model"] == "gemini-test-model"
    assert captured["api_key"] == "test-key"
    assert "wages" in str(captured["contents"])

    get_settings.cache_clear()


def test_generate_structured_response_returns_timeout_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    class FakeModels:
        def generate_content(self, *, model: str, contents: str, config: object) -> object:
            raise httpx.TimeoutException("timed out")

    class FakeClient:
        def __init__(self, *, api_key: str, http_options: object) -> None:
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)

    response = generate_structured_agent_response(
        system_prompt="Return JSON.",
        user_payload={"redacted": True},
        response_schema_name="ChatResponse",
    )

    assert response["status"] == "fallback"
    assert response["response_schema_name"] == "ChatResponse"
    assert response["retryable"] is True
    assert "timed out" in response["message"]

    get_settings.cache_clear()


def test_generate_structured_response_returns_parse_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    class FakeModels:
        def generate_content(self, *, model: str, contents: str, config: object) -> object:
            return SimpleNamespace(text="not json")

    class FakeClient:
        def __init__(self, *, api_key: str, http_options: object) -> None:
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)

    response = generate_structured_agent_response(
        system_prompt="Return JSON.",
        user_payload={"redacted": True},
        response_schema_name="ChatResponse",
    )

    assert response["status"] == "fallback"
    assert response["retryable"] is False
    assert "could not be parsed" in response["message"]

    get_settings.cache_clear()
