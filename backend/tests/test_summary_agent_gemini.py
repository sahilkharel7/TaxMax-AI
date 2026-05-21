from decimal import Decimal
from typing import Any

import pytest

from app.agents import summary_agent
from app.agents.summary_agent import SummaryAgent
from app.schemas import IncomeInput, TaxScenarioRequest, TaxpayerProfile
from app.services.gemini_client import GeminiNotConfiguredError
from app.services.tax_rule_service import get_tax_rule_context_dict


def test_summary_agent_uses_deterministic_fallback_when_gemini_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_not_configured(
        system_prompt: str,
        user_payload: dict[str, Any],
        response_schema_name: str,
    ) -> dict[str, Any]:
        raise GeminiNotConfiguredError("missing key")

    monkeypatch.setattr(
        "app.services.gemini_client.generate_structured_agent_response",
        raise_not_configured,
    )
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(tax_year=2025, filing_status="single"),
    )

    findings, warnings = SummaryAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025),
    )

    assert any("Initial review context includes" in finding.summary for finding in findings)
    assert any(warning.code == "SUMMARY_MISSING_INFORMATION" for warning in warnings)


def test_summary_agent_uses_deterministic_fallback_when_gemini_returns_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def return_fallback(
        system_prompt: str,
        user_payload: dict[str, Any],
        response_schema_name: str,
    ) -> dict[str, Any]:
        return {
            "status": "fallback",
            "response_schema_name": response_schema_name,
            "message": "Gemini unavailable.",
            "retryable": True,
        }

    monkeypatch.setattr(
        "app.services.gemini_client.generate_structured_agent_response",
        return_fallback,
    )
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="CA",
        ),
    )

    findings, warnings = SummaryAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025, "CA"),
    )

    assert warnings
    assert any("Initial review context includes" in finding.summary for finding in findings)


def test_summary_agent_sends_only_sanitized_fields_to_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payload: dict[str, Any] = {}

    def return_summary(
        system_prompt: str,
        user_payload: dict[str, Any],
        response_schema_name: str,
    ) -> dict[str, Any]:
        captured_payload.update(user_payload)
        return {
            "summary": "Education and income review may apply and requires confirmation before filing decisions.",
        }

    monkeypatch.setattr(
        "app.services.gemini_client.generate_structured_agent_response",
        return_summary,
    )
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="CA",
            can_be_claimed_as_dependent=False,
        ),
        income=IncomeInput(
            w2_wages=Decimal("64500.00"),
            federal_withholding=Decimal("7200.00"),
        ),
    )

    findings, warnings = SummaryAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025, "CA"),
    )

    assert warnings == []
    assert findings[0].summary == (
        "Education and income review may apply and requires confirmation before filing decisions."
    )
    assert captured_payload["income_field_presence"] == {
        "w2_wages": True,
        "federal_withholding": True,
        "state_withholding": False,
        "interest_income": False,
        "self_employment_income": False,
        "other_income": False,
    }
    assert "64500.00" not in str(captured_payload)
    assert "7200.00" not in str(captured_payload)
