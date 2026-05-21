"""End-to-end tests for /api/tax/analyze.

Drives the orchestrator through the API layer and asserts the structured
contract required by the product spec:

- Status 200 with TaxAnalysisResponse shape (findings, warnings, next_questions,
  missing_information, disclaimer).
- Cautious wording only ("may", "needs review", "requires confirmation").
- No "you qualify" / "guaranteed refund" / "you will receive" claims.
- No fake refund or tax-due numbers fabricated by agents.
- Federal Tax / State Tax / Deduction / Credit / Optimization / Risk / Summary
  agents are present in the orchestrator output for a complete scenario.
- Critical signals from the QA spec are surfaced:
    * Unknown dependency status -> dependency review warning.
    * 1098-T present -> education credit review finding.
    * Document with extraction_status == "needs_review" -> review warning.
"""

from __future__ import annotations

import re
from copy import deepcopy

from fastapi.testclient import TestClient

from app.main import app
from app.services.agent_orchestrator import AGENTS


client = TestClient(app)


SPEC_SCENARIO: dict = {
    "profile": {
        "filing_status": "single",
        "tax_year": 2025,
        "resident_state": "NY",
        "work_state": "NY",
        "can_be_claimed_as_dependent": None,
        "was_student": True,
        "received_1098_t": True,
        "multiple_jobs": False,
        "received_1099": False,
    },
    "income": {
        "w2_wages": "42350.00",
        "federal_withholding": "4280.00",
        "interest_income": "120.00",
    },
    "education": {
        "is_student": True,
        "received_1098_t": True,
        "qualified_expenses": "18500.00",
        "scholarships_or_grants": "7500.00",
        "institution_name": "Columbia University",
    },
    "documents": [
        {
            "document_id": "doc_w2_001",
            "document_type": "w2",
            "file_name": "sample-w2.pdf",
            "extraction_status": "parsed",
        },
        {
            "document_id": "doc_1098t_001",
            "document_type": "1098_t",
            "file_name": "sample-1098t.pdf",
            "extraction_status": "needs_review",
        },
    ],
    "user_goal": "Help me review my W-2 and 1098-T before I file.",
}


CAUTIOUS_PHRASES = (
    "may apply",
    "may be eligible",
    "needs review",
    "requires confirmation",
    "needs confirmation",
    "should be reviewed",
    "may need",
    "needs additional",
)

UNSAFE_PHRASES = (
    "you qualify",
    "you definitely qualify",
    "you will qualify",
    "guaranteed refund",
    "guaranteed to receive",
    "you will receive",
    "you are entitled to",
    "you definitely",
    "100% refund",
)


def _post_spec_scenario() -> dict:
    response = client.post("/api/tax/analyze", json=deepcopy(SPEC_SCENARIO))
    assert response.status_code == 200, response.text
    return response.json()


def _flatten_text(payload: dict) -> str:
    parts: list[str] = []

    def _walk(node):
        if isinstance(node, dict):
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)
        elif isinstance(node, str):
            parts.append(node)

    _walk(payload)
    return " \n ".join(parts).lower()


def test_analyze_returns_structured_taxanalysis_response_shape() -> None:
    payload = _post_spec_scenario()

    for key in (
        "status",
        "findings",
        "warnings",
        "next_questions",
        "missing_information",
        "disclaimer",
    ):
        assert key in payload, f"Missing key {key!r} in response"

    assert payload["status"] in {"draft", "review_required", "needs_more_information"}
    assert isinstance(payload["findings"], list)
    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["next_questions"], list)
    assert isinstance(payload["missing_information"], list)
    assert payload["disclaimer"]
    assert "qualified" in payload["disclaimer"].lower() or "professional" in payload["disclaimer"].lower()


def test_analyze_runs_full_agent_lineup_in_specified_order() -> None:
    expected_order = [
        "Federal Tax Agent",
        "State Tax Agent",
        "Deduction Agent",
        "Credit Agent",
        "Optimization Agent",
        "Risk Review Agent",
        "Summary Agent",
    ]
    actual_order = [agent.agent_name for agent in AGENTS]
    assert actual_order == expected_order, actual_order

    payload = _post_spec_scenario()
    seen_agents = {finding["agent_name"] for finding in payload["findings"]}
    for required in (
        "Federal Tax Agent",
        "State Tax Agent",
        "Credit Agent",
    ):
        assert required in seen_agents, (required, seen_agents)


def test_analyze_flags_unknown_dependency_status() -> None:
    payload = _post_spec_scenario()
    warning_codes = {warning["code"] for warning in payload["warnings"]}

    assert (
        "MISSING_DEPENDENCY_CONTEXT" in warning_codes
        or "MISSING_DEPENDENT_STATUS" in warning_codes
        or "EDUCATION_DEPENDENCY_UNKNOWN" in warning_codes
    ), warning_codes
    assert "Dependency status" in payload["missing_information"]


def test_analyze_flags_education_credit_review_when_1098t_present() -> None:
    payload = _post_spec_scenario()
    education_credit_findings = [
        finding
        for finding in payload["findings"]
        if finding["category"] == "credits"
        and "education credit" in finding["summary"].lower()
    ]

    assert education_credit_findings, payload["findings"]
    assert all(
        any(phrase in finding["summary"].lower() for phrase in CAUTIOUS_PHRASES)
        for finding in education_credit_findings
    )


def test_analyze_flags_document_needing_review() -> None:
    payload = _post_spec_scenario()

    review_findings = [
        finding
        for finding in payload["findings"]
        if finding["category"] == "documents" and "review" in finding["summary"].lower()
    ]
    review_warnings = [
        warning
        for warning in payload["warnings"]
        if warning["code"] == "DOCUMENT_EXTRACTION_NEEDS_REVIEW"
    ]

    assert review_findings or review_warnings, payload


def test_analyze_uses_cautious_wording_and_no_final_eligibility_claims() -> None:
    payload = _post_spec_scenario()
    text = _flatten_text(payload)

    for phrase in UNSAFE_PHRASES:
        assert phrase not in text, f"Unsafe phrase leaked into response: {phrase!r}"

    assert any(phrase in text for phrase in CAUTIOUS_PHRASES), text


def test_analyze_does_not_invent_dollar_refund_or_tax_due() -> None:
    payload = _post_spec_scenario()
    text = _flatten_text(payload)

    forbidden_patterns = [
        r"refund of \$",
        r"refund: \$",
        r"you (will|should) get \$",
        r"tax due of \$",
        r"you owe \$",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), f"Fabricated dollar claim: {pattern}"


def test_analyze_with_missing_state_rule_file_returns_controlled_warning() -> None:
    scenario = deepcopy(SPEC_SCENARIO)
    scenario["profile"]["tax_year"] = 2024
    scenario["profile"]["resident_state"] = "NY"

    response = client.post("/api/tax/analyze", json=scenario)

    assert response.status_code == 200
    payload = response.json()
    warning_codes = {warning["code"] for warning in payload["warnings"]}
    assert (
        "TAX_RULE_FILE_MISSING" in warning_codes
        or "FEDERAL_RULE_CONTEXT_UNAVAILABLE" in warning_codes
    ), warning_codes


def test_analyze_minimal_scenario_completes_without_500() -> None:
    minimal = {
        "profile": {
            "filing_status": "single",
            "tax_year": 2025,
            "resident_state": "CA",
            "can_be_claimed_as_dependent": False,
        },
        "documents": [],
    }
    response = client.post("/api/tax/analyze", json=minimal)

    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"]
    assert payload["status"] in {"draft", "review_required", "needs_more_information"}
