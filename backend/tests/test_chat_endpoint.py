"""Strict QA tests for /api/chat.

Coverage:
- Educational topics (W-2, 1098-T) get topic-specific replies.
- Adversarial prompts (e-filing, exact refund, "do I qualify") get refusals
  with cautious wording and never the banned final-claim phrases.
- Empty / oversized messages return 422.
- Scenario context surfaces structured warnings and missing_information.
- Every response carries the disclaimer.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


BANNED_PHRASES = (
    "you qualify",
    "you definitely qualify",
    "you will qualify",
    "guaranteed refund",
    "you will receive a refund",
    "you are entitled",
    "i will file",
    "we will file",
)


def _post(message: str, scenario: dict | None = None) -> dict:
    response = client.post(
        "/api/chat",
        json={"message": message} | ({"scenario": scenario} if scenario else {}),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _assert_safe(answer: str) -> None:
    lowered = answer.lower()
    for phrase in BANNED_PHRASES:
        assert phrase not in lowered, f"Banned phrase leaked: {phrase!r}"


def test_chat_explains_w2() -> None:
    payload = _post("What is a W-2?")
    answer = payload["answer"]
    assert "W-2" in answer or "wage" in answer.lower()
    _assert_safe(answer)
    assert payload["disclaimer"]


def test_chat_explains_1098t() -> None:
    payload = _post("What is a 1098-T?")
    answer = payload["answer"].lower()
    assert "1098-t" in answer or "tuition" in answer
    _assert_safe(answer)


def test_chat_default_reply_when_topic_unrecognized() -> None:
    payload = _post("Hello there.")
    answer = payload["answer"].lower()
    assert "qualified tax professional" in answer or "tax terms" in answer
    _assert_safe(answer)


def test_chat_refuses_e_filing_request() -> None:
    payload = _post("Can you file my taxes with the IRS?")
    answer = payload["answer"].lower()

    assert "cannot file" in answer or "not available" in answer
    assert "irs" in answer or "e-file" in answer or "e-filing" in answer
    _assert_safe(answer)


def test_chat_refuses_exact_refund_demand() -> None:
    payload = _post("Tell me exactly how much refund I will get.")
    answer = payload["answer"].lower().replace("\u2019", "'")

    assert "cannot" in answer or "can't" in answer or "not final" in answer
    _assert_safe(answer)
    assert "guaranteed" not in answer


def test_chat_handles_qualify_question_cautiously() -> None:
    payload = _post("Do I qualify for the education credit?")
    answer = payload["answer"].lower().replace("\u2019", "'")

    _assert_safe(answer)
    assert (
        "may" in answer
        or "needs review" in answer
        or "requires" in answer
        or "cannot" in answer
        or "can't" in answer
        or "professional" in answer
    )


def test_chat_rejects_empty_message() -> None:
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_rejects_oversized_message() -> None:
    response = client.post("/api/chat", json={"message": "x" * 5000})
    assert response.status_code == 422


def test_chat_with_scenario_flags_missing_information() -> None:
    payload = _post(
        "Did I provide enough information?",
        scenario={
            "profile": {
                "filing_status": None,
                "tax_year": None,
                "was_student": True,
                "received_1098_t": None,
            }
        },
    )

    assert payload["status"] == "needs_more_information"
    assert "Tax year" in payload["missing_information"]
    assert "Filing status" in payload["missing_information"]
    assert any(w["code"] == "MISSING_1098_T_STATUS" for w in payload["warnings"])


def test_chat_response_always_includes_disclaimer() -> None:
    for prompt in (
        "What is Box 1?",
        "What documents should I upload?",
        "How do filing statuses work?",
        "Should I review the parsed values?",
    ):
        payload = _post(prompt)
        assert payload["disclaimer"], prompt
        _assert_safe(payload["answer"])
