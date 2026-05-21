from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _minimal_scenario() -> dict:
    return {
        "profile": {
            "filing_status": "single",
            "tax_year": 2025,
            "resident_state": "CA",
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


def test_analyze_returns_structured_response_for_supported_year() -> None:
    response = client.post("/api/tax/analyze", json=_minimal_scenario())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"draft", "review_required", "needs_more_information"}
    assert payload["disclaimer"]
    assert any(f["agent_name"] == "Income Agent" for f in payload["findings"])
    assert any(f["agent_name"] == "Rule Context Agent" for f in payload["findings"])


def test_analyze_flags_missing_filing_status_and_year() -> None:
    scenario = _minimal_scenario()
    scenario["profile"]["filing_status"] = None
    scenario["profile"]["tax_year"] = None

    response = client.post("/api/tax/analyze", json=scenario)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_more_information"
    assert "Filing status" in payload["missing_information"]
    assert "Tax year" in payload["missing_information"]


def test_analyze_surfaces_education_findings_for_student() -> None:
    scenario = _minimal_scenario()
    scenario["profile"]["was_student"] = True
    scenario["profile"]["received_1098_t"] = True
    scenario["education"] = {
        "is_student": True,
        "received_1098_t": True,
        "qualified_expenses": "3800.00",
        "scholarships_or_grants": "500.00",
        "institution_name": "Example State University",
    }

    response = client.post("/api/tax/analyze", json=scenario)

    assert response.status_code == 200
    payload = response.json()
    assert any(f["agent_name"] == "Education Agent" for f in payload["findings"])


def test_analyze_warns_on_missing_rule_file() -> None:
    scenario = _minimal_scenario()
    scenario["profile"]["tax_year"] = 2024

    response = client.post("/api/tax/analyze", json=scenario)

    assert response.status_code == 200
    payload = response.json()
    assert any(w["code"] == "TAX_RULE_FILE_MISSING" for w in payload["warnings"])


def test_tax_rules_endpoint_returns_loaded_payload() -> None:
    response = client.get("/api/tax/rules", params={"tax_year": 2025, "state_code": "CA"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["tax_year"] == 2025
    assert payload["state_code"] == "CA"
    assert payload["federal"]["jurisdiction"] == "US"


def test_tax_rules_endpoint_returns_error_payload_for_missing_year() -> None:
    response = client.get("/api/tax/rules", params={"tax_year": 2024})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["code"] == "TAX_RULE_FILE_MISSING"
