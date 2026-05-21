from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


SCENARIO = {
    "profile": {
        "filing_status": "single",
        "tax_year": 2025,
        "resident_state": "NY",
        "work_state": "CA",
        "can_be_claimed_as_dependent": False,
        "was_student": True,
        "received_1098_t": True,
        "multiple_jobs": False,
        "received_1099": True,
        "dependents_count": 1,
    },
    "income": {
        "w2_wages": "42000.00",
        "federal_withholding": "4200.00",
        "self_employment_income": "6000.00",
    },
    "education": {
        "is_student": True,
        "received_1098_t": True,
        "qualified_expenses": "8000.00",
        "student_loan_interest": "900.00",
    },
    "itemized_deductions": {
        "charitable_cash": "700.00",
        "state_local_taxes_paid": "3000.00",
    },
    "self_employment": {
        "gross_income": "6000.00",
        "expenses": "1200.00",
        "has_1099_nec": True,
    },
    "documents": [
        {
            "document_type": "1098_t",
            "file_name": "sample-1098t.pdf",
            "extraction_status": "needs_review",
        }
    ],
    "user_goal": "Find legal tax-saving opportunities.",
}


def test_optimize_returns_structured_opportunities() -> None:
    response = client.post("/api/tax/optimize", json=SCENARIO)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] in {"draft", "review_required", "needs_more_information"}
    assert payload["opportunities"]
    assert payload["disclaimer"]
    first = payload["opportunities"][0]
    for key in (
        "opportunity_id",
        "agent_name",
        "category",
        "title",
        "summary",
        "potential_impact",
        "required_facts",
        "required_documents",
        "risk_level",
        "suggested_next_step",
    ):
        assert key in first


def test_optimize_surfaces_expected_savings_review_areas() -> None:
    response = client.post("/api/tax/optimize", json=SCENARIO)
    payload = response.json()
    ids = {item["opportunity_id"] for item in payload["opportunities"]}

    assert "credit_education_review" in ids
    assert "deduction_self_employment_expenses" in ids
    assert "state_multistate_review" in ids
    assert "documentation_confirm_extracted_fields" in ids


def test_optimize_uses_cautious_wording() -> None:
    response = client.post("/api/tax/optimize", json=SCENARIO)
    text = response.text.lower()

    banned = (
        "you qualify",
        "guaranteed refund",
        "you will save",
        "you are eligible",
        "claim this deduction",
    )
    for phrase in banned:
        assert phrase not in text
    assert "may" in text or "requires confirmation" in text


def test_optimize_missing_profile_context_needs_more_information() -> None:
    response = client.post(
        "/api/tax/optimize",
        json={"profile": {"tax_year": 2025}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_more_information"
    assert "Filing status" in payload["missing_information"]
    assert "Resident state" in payload["missing_information"]
