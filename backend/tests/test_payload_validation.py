"""Strict payload validation tests for /api/tax/analyze and /api/chat.

Pydantic must reject malformed payloads with 422 before they reach any agent.
None of the failure paths should leak stack traces or environment-derived
strings (paths, secrets) to the client.
"""

from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


VALID_ANALYZE_PAYLOAD: dict = {
    "profile": {
        "filing_status": "single",
        "tax_year": 2025,
        "resident_state": "NY",
        "work_state": "NY",
        "can_be_claimed_as_dependent": False,
        "was_student": False,
        "received_1098_t": False,
        "multiple_jobs": False,
        "received_1099": False,
    },
    "income": {
        "w2_wages": "42350.00",
        "federal_withholding": "4280.00",
    },
    "documents": [],
}


def _payload(**profile_overrides) -> dict:
    payload = deepcopy(VALID_ANALYZE_PAYLOAD)
    payload["profile"].update(profile_overrides)
    return payload


def _assert_no_stack_trace(text: str) -> None:
    forbidden = [
        "Traceback",
        "File \"/",
        "site-packages",
        ".venv/",
        "/Users/",
    ]
    for needle in forbidden:
        assert needle not in text, f"Stack-trace fragment leaked: {needle!r}"


def test_analyze_rejects_empty_body() -> None:
    response = client.post("/api/tax/analyze", json={})

    assert response.status_code == 422
    _assert_no_stack_trace(response.text)
    assert response.json()["detail"]


def test_analyze_rejects_missing_profile() -> None:
    response = client.post(
        "/api/tax/analyze",
        json={"income": {"w2_wages": "10000.00"}},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("profile" in str(item).lower() for item in detail)


def test_analyze_rejects_null_profile() -> None:
    response = client.post(
        "/api/tax/analyze",
        json={"profile": None, "income": {"w2_wages": "10000.00"}},
    )

    assert response.status_code == 422


def test_analyze_rejects_invalid_filing_status() -> None:
    response = client.post(
        "/api/tax/analyze",
        json=_payload(filing_status="married-with-cats"),
    )

    assert response.status_code == 422


def test_analyze_rejects_string_tax_year() -> None:
    response = client.post(
        "/api/tax/analyze",
        json=_payload(tax_year="not-a-year"),
    )

    assert response.status_code == 422


def test_analyze_rejects_out_of_range_tax_year() -> None:
    response = client.post(
        "/api/tax/analyze",
        json=_payload(tax_year=1899),
    )
    assert response.status_code == 422

    response = client.post(
        "/api/tax/analyze",
        json=_payload(tax_year=2999),
    )
    assert response.status_code == 422


def test_analyze_rejects_negative_w2_wages() -> None:
    payload = _payload()
    payload["income"]["w2_wages"] = "-100.00"

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_negative_federal_withholding() -> None:
    payload = _payload()
    payload["income"]["federal_withholding"] = "-1.00"

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_invalid_state_code_too_short() -> None:
    response = client.post(
        "/api/tax/analyze",
        json=_payload(resident_state="N"),
    )
    assert response.status_code == 422


def test_analyze_rejects_invalid_state_code_too_long() -> None:
    response = client.post(
        "/api/tax/analyze",
        json=_payload(resident_state="NEW YORK"),
    )
    assert response.status_code == 422


def test_analyze_rejects_unsupported_document_type() -> None:
    payload = deepcopy(VALID_ANALYZE_PAYLOAD)
    payload["documents"] = [
        {
            "document_type": "k1_partnership",
            "file_name": "k1.pdf",
        }
    ]

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code == 422
    _assert_no_stack_trace(response.text)


def test_analyze_rejects_invalid_document_extraction_status() -> None:
    payload = deepcopy(VALID_ANALYZE_PAYLOAD)
    payload["documents"] = [
        {
            "document_type": "w2",
            "extraction_status": "definitely_done",
        }
    ]

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_ignores_unknown_top_level_fields_safely() -> None:
    payload = deepcopy(VALID_ANALYZE_PAYLOAD)
    payload["unknown_extra_field"] = "<script>alert(1)</script>"

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code == 200
    body_text = response.text
    assert "<script>alert(1)</script>" not in body_text
    assert "unknown_extra_field" not in body_text


def test_analyze_rejects_extremely_large_user_goal() -> None:
    payload = deepcopy(VALID_ANALYZE_PAYLOAD)
    payload["user_goal"] = "x" * 200_000

    response = client.post("/api/tax/analyze", json=payload)

    assert response.status_code in {200, 413, 422}
    _assert_no_stack_trace(response.text)


def test_chat_rejects_empty_message() -> None:
    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422
    _assert_no_stack_trace(response.text)


def test_chat_rejects_huge_message() -> None:
    response = client.post(
        "/api/chat",
        json={"message": "a" * 5000},
    )

    assert response.status_code == 422
    _assert_no_stack_trace(response.text)


def test_chat_rejects_missing_message() -> None:
    response = client.post("/api/chat", json={})

    assert response.status_code == 422


def test_chat_rejects_non_string_message() -> None:
    response = client.post("/api/chat", json={"message": 123})

    assert response.status_code == 422


def test_tax_rules_query_rejects_invalid_year() -> None:
    response = client.get("/api/tax/rules", params={"tax_year": "abc"})
    assert response.status_code == 422

    response = client.get("/api/tax/rules", params={"tax_year": 1500})
    assert response.status_code == 422
