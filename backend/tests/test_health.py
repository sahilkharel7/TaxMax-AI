from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "TaxMax AI API",
    }
    assert "gemini_api_key" not in response.json()
    assert "GEMINI_API_KEY" not in response.text
