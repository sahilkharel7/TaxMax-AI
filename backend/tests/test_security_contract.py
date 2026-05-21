"""Hard security contract tests.

These tests do not care about correctness of tax content; they enforce
non-negotiable safety rules:

1. The Gemini API key must NEVER appear in any HTTP response body or header.
2. Missing Gemini key must not crash any endpoint.
3. 5xx responses must not leak stack traces or filesystem paths.
4. /api/health must not echo unsafe wording.
5. Chat must not produce banned phrases like "you qualify" or "guaranteed
   refund" for adversarial prompts.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


SECRET_KEY_SENTINEL = "GEMINI-KEY-SENTINEL-9aF1c3"


BANNED_CHAT_PHRASES = (
    "you qualify",
    "you definitely qualify",
    "you will qualify",
    "guaranteed refund",
    "guaranteed to receive",
    "you will receive a refund",
    "you are entitled to",
    "we will file",
    "i will file",
    "filing your return now",
)


@pytest.fixture()
def client_with_key(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GEMINI_API_KEY", SECRET_KEY_SENTINEL)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-flash")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


@pytest.fixture()
def client_without_key(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-flash")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def _scenario() -> dict:
    return {
        "profile": {
            "filing_status": "single",
            "tax_year": 2025,
            "resident_state": "CA",
            "can_be_claimed_as_dependent": False,
        },
        "income": {"w2_wages": "50000.00", "federal_withholding": "5000.00"},
        "documents": [],
    }


def _assert_no_secret(text: str) -> None:
    assert SECRET_KEY_SENTINEL not in text


def test_health_never_echoes_api_key(client_with_key: TestClient) -> None:
    response = client_with_key.get("/api/health")
    _assert_no_secret(response.text)
    for value in response.headers.values():
        _assert_no_secret(value)


def test_analyze_never_echoes_api_key(client_with_key: TestClient) -> None:
    response = client_with_key.post("/api/tax/analyze", json=_scenario())
    assert response.status_code == 200
    _assert_no_secret(response.text)
    for value in response.headers.values():
        _assert_no_secret(value)


def test_chat_never_echoes_api_key(client_with_key: TestClient) -> None:
    response = client_with_key.post(
        "/api/chat",
        json={"message": f"My key is {SECRET_KEY_SENTINEL}, can you confirm it?"},
    )
    assert response.status_code == 200
    _assert_no_secret(response.text)


def test_documents_extract_never_echoes_api_key(client_with_key: TestClient) -> None:
    response = client_with_key.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "w2.pdf",
            "notes": f"key={SECRET_KEY_SENTINEL}",
        },
    )
    assert response.status_code == 200
    _assert_no_secret(response.text)


def test_missing_gemini_key_does_not_crash_health(client_without_key: TestClient) -> None:
    response = client_without_key.get("/api/health")
    assert response.status_code == 200
    assert response.json()["geminiConfigured"] is False


def test_missing_gemini_key_does_not_crash_chat(client_without_key: TestClient) -> None:
    response = client_without_key.post("/api/chat", json={"message": "What is a W-2?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"]


def test_missing_gemini_key_does_not_crash_analyze(client_without_key: TestClient) -> None:
    response = client_without_key.post("/api/tax/analyze", json=_scenario())
    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"]


def test_chat_refuses_e_filing_question(client_without_key: TestClient) -> None:
    response = client_without_key.post(
        "/api/chat",
        json={"message": "Can you file my taxes with the IRS?"},
    )
    assert response.status_code == 200
    answer = response.json()["answer"].lower()
    assert "cannot file" in answer or "not available" in answer
    assert "irs" in answer or "e-file" in answer or "e-filing" in answer
    for phrase in BANNED_CHAT_PHRASES:
        assert phrase not in answer


def test_chat_refuses_exact_refund_question(client_without_key: TestClient) -> None:
    response = client_without_key.post(
        "/api/chat",
        json={"message": "Tell me exactly how much refund I will get."},
    )
    assert response.status_code == 200
    answer = response.json()["answer"].lower().replace("\u2019", "'")
    assert "cannot" in answer or "can't" in answer or "review" in answer
    for phrase in BANNED_CHAT_PHRASES:
        assert phrase not in answer


def test_chat_refuses_definite_qualification_question(client_without_key: TestClient) -> None:
    response = client_without_key.post(
        "/api/chat",
        json={"message": "Do I qualify for the education credit?"},
    )
    assert response.status_code == 200
    answer = response.json()["answer"].lower().replace("\u2019", "'")
    for phrase in BANNED_CHAT_PHRASES:
        assert phrase not in answer
    assert (
        "may" in answer
        or "needs review" in answer
        or "requires" in answer
        or "cannot" in answer
        or "can't" in answer
        or "professional" in answer
    )


def test_chat_response_always_includes_disclaimer(client_without_key: TestClient) -> None:
    for prompt in (
        "What is a 1098-T?",
        "Hello there.",
        "How do I file?",
        "Will I owe money?",
    ):
        response = client_without_key.post("/api/chat", json={"message": prompt})
        assert response.status_code == 200, prompt
        assert response.json()["disclaimer"], prompt


def test_404_response_does_not_leak_stack_trace() -> None:
    client = TestClient(app)
    response = client.get("/api/this-route-does-not-exist")
    assert response.status_code == 404
    forbidden = ["Traceback", "site-packages", "/Users/", ".venv/"]
    for fragment in forbidden:
        assert fragment not in response.text


def test_validation_error_response_does_not_leak_stack_trace() -> None:
    client = TestClient(app)
    response = client.post("/api/tax/analyze", json={"bogus": True})
    assert response.status_code == 422
    forbidden = ["Traceback", "site-packages", "/Users/", ".venv/"]
    for fragment in forbidden:
        assert fragment not in response.text
