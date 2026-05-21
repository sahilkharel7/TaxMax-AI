from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_topic_specific_reply_without_scenario() -> None:
    response = client.post("/api/chat", json={"message": "What is a W-2?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft"
    assert "W-2" in payload["answer"] or "wage" in payload["answer"].lower()
    assert payload["next_questions"]
    assert payload["disclaimer"]


def test_chat_default_reply_when_topic_unrecognized() -> None:
    response = client.post(
        "/api/chat",
        json={"message": "Hello there."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "qualified tax professional" in payload["answer"].lower()


def test_chat_flags_missing_information_from_scenario() -> None:
    response = client.post(
        "/api/chat",
        json={
            "message": "Did I provide enough information?",
            "scenario": {
                "profile": {
                    "filing_status": None,
                    "tax_year": None,
                    "was_student": True,
                    "received_1098_t": None,
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_more_information"
    assert "Tax year" in payload["missing_information"]
    assert "Filing status" in payload["missing_information"]
    assert any(w["code"] == "MISSING_1098_T_STATUS" for w in payload["warnings"])


def test_chat_rejects_empty_message() -> None:
    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422
