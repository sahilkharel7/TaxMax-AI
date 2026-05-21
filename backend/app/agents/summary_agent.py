from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent, rule_context_has_error
from app.schemas import TaxScenarioRequest


SUMMARY_SYSTEM_PROMPT = """
You are TaxMax AI's summary agent.
Write one concise plain-language summary for a tax preparation review.
Use cautious wording such as "may apply", "needs review", and "requires confirmation".
Do not calculate tax, estimate refunds, estimate tax owed, or claim final eligibility.
Return JSON only with this shape: {"summary": "plain-language summary"}.
"""


class SummaryAgent(BaseTaxAgent):
    """Produces cautious high-level summary findings."""

    agent_name = "Summary Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        completed_inputs, missing_inputs = _input_status(scenario)
        findings = self._summary_findings(
            scenario=scenario,
            tax_rule_context=tax_rule_context,
            completed_inputs=completed_inputs,
        )
        warnings = []

        if missing_inputs:
            warnings.append(
                self.warning(
                    code="SUMMARY_MISSING_INFORMATION",
                    message=f"Missing information needs review: {', '.join(missing_inputs)}.",
                    severity="medium",
                    recommended_follow_up="Ask the user to provide the missing items before treating the analysis as complete.",
                )
            )

        return findings, warnings

    def _summary_findings(
        self,
        *,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
        completed_inputs: list[str],
    ) -> list[Any]:
        gemini_summary = self._gemini_summary(scenario, tax_rule_context)
        if gemini_summary:
            return [
                self.finding(
                    category="summary",
                    summary=gemini_summary,
                    confidence="medium",
                    rationale="Gemini generated a plain-language summary from sanitized scenario fields.",
                    suggested_action="Use this as a preparation checklist and confirm all facts before filing decisions.",
                )
            ]

        if not completed_inputs:
            return []

        return [
            self.finding(
                category="summary",
                summary=f"Initial review context includes {', '.join(completed_inputs)} and still needs confirmation.",
                confidence="medium",
                rationale="The summary agent only reports which inputs are present; it does not calculate taxes or determine eligibility.",
                suggested_action="Use this as a preparation checklist before running deeper review.",
            )
        ]

    def _gemini_summary(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> str | None:
        try:
            from app.services.gemini_client import (
                GeminiNotConfiguredError,
                generate_structured_agent_response,
            )
        except ImportError:
            return None

        try:
            response = generate_structured_agent_response(
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_payload=_sanitized_summary_payload(scenario, tax_rule_context),
                response_schema_name="SummaryAgentPlainLanguageSummary",
            )
        except GeminiNotConfiguredError:
            return None

        if response.get("status") == "fallback":
            return None

        summary = response.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            return None

        return summary.strip()


def _input_status(scenario: TaxScenarioRequest) -> tuple[list[str], list[str]]:
    completed_inputs = []
    missing_inputs = []

    if scenario.profile.tax_year is None:
        missing_inputs.append("tax year")
    else:
        completed_inputs.append("tax year")

    if scenario.profile.filing_status is None:
        missing_inputs.append("filing status")
    else:
        completed_inputs.append("filing status")

    if scenario.income is None:
        missing_inputs.append("income details")
    else:
        completed_inputs.append("income details")

    if scenario.profile.resident_state is None:
        missing_inputs.append("resident state")
    else:
        completed_inputs.append("resident state")

    return completed_inputs, missing_inputs


def _sanitized_summary_payload(
    scenario: TaxScenarioRequest,
    tax_rule_context: dict[str, Any],
) -> dict[str, Any]:
    income = scenario.income
    education = scenario.education

    return {
        "tax_year": scenario.profile.tax_year,
        "filing_status": scenario.profile.filing_status,
        "resident_state_present": scenario.profile.resident_state is not None,
        "work_state_differs_from_resident": bool(
            scenario.profile.resident_state
            and scenario.profile.work_state
            and scenario.profile.resident_state.upper() != scenario.profile.work_state.upper()
        ),
        "dependent_status_known": scenario.profile.can_be_claimed_as_dependent is not None,
        "has_income_input": income is not None,
        "income_field_presence": {
            "w2_wages": bool(income and income.w2_wages is not None),
            "federal_withholding": bool(income and income.federal_withholding is not None),
            "state_withholding": bool(income and income.state_withholding is not None),
            "interest_income": bool(income and income.interest_income is not None),
            "self_employment_income": bool(income and income.self_employment_income is not None),
            "other_income": bool(income and income.other_income is not None),
        },
        "education_context": {
            "is_student": education.is_student if education else None,
            "received_1098_t": (
                education.received_1098_t
                if education
                else scenario.profile.received_1098_t
            ),
            "has_qualified_expenses_input": bool(
                education and education.qualified_expenses is not None
            ),
            "has_scholarships_or_grants_input": bool(
                education and education.scholarships_or_grants is not None
            ),
            "institution_name_present": bool(education and education.institution_name),
        },
        "document_types": sorted({document.document_type for document in scenario.documents}),
        "document_statuses": sorted(
            {
                document.extraction_status
                for document in scenario.documents
                if document.extraction_status is not None
            }
        ),
        "tax_rule_context_available": not rule_context_has_error(tax_rule_context),
    }
