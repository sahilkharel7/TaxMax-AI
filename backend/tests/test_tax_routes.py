from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_route_accepts_valid_payload() -> None:
    response = client.post(
        "/api/tax/analyze",
        json={
            "profile": {
                "tax_year": 2025,
                "filing_status": "single",
                "resident_state": "CA",
                "can_be_claimed_as_dependent": False,
                "received_1098_t": True,
            },
            "education": {
                "received_1098_t": True,
            },
            "user_goal": "Review my education documents.",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] in {"draft", "needs_more_information", "review_required"}
    assert "findings" in body
    assert "warnings" in body
    assert "next_questions" in body
    assert "missing_information" in body
    assert any(finding["category"] == "credits" for finding in body["findings"])


def test_analyze_route_rejects_invalid_payload() -> None:
    response = client.post(
        "/api/tax/analyze",
        json={
            "education": {
                "received_1098_t": True,
            }
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]
