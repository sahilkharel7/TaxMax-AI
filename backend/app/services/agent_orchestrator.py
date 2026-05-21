from __future__ import annotations

from typing import Any

from app.agents import (
    CreditAgent,
    DeductionAgent,
    FederalTaxAgent,
    OptimizationAgent,
    RiskReviewAgent,
    StateTaxAgent,
    SummaryAgent,
)
from app.schemas import AgentFinding, AgentWarning, TaxAnalysisResponse, TaxScenarioRequest
from app.services.tax_rule_service import get_tax_rule_context


AGENTS = [
    FederalTaxAgent(),
    StateTaxAgent(),
    DeductionAgent(),
    CreditAgent(),
    OptimizationAgent(),
    RiskReviewAgent(),
    SummaryAgent(),
]

MISSING_INFORMATION_BY_WARNING_CODE = {
    "MISSING_TAX_YEAR": "Tax year",
    "MISSING_FILING_STATUS": "Filing status",
    "MISSING_DEDUCTION_FILING_STATUS": "Filing status",
    "MISSING_INCOME_CONTEXT": "Income details",
    "MISSING_RESIDENT_STATE": "Resident state",
    "MISSING_DEPENDENCY_CONTEXT": "Dependency status",
    "MISSING_DEPENDENT_STATUS": "Dependency status",
    "MISSING_1098_T_CONFIRMATION": "Form 1098-T confirmation",
    "MISSING_USER_GOAL": "User goal",
    "SUMMARY_MISSING_INFORMATION": "Summary missing information",
}


def analyze_tax_scenario(request: TaxScenarioRequest) -> TaxAnalysisResponse:
    """Run deterministic TaxMax AI agents and merge their outputs."""

    tax_rule_context = _load_tax_rule_context(request)
    findings: list[AgentFinding] = []
    warnings: list[AgentWarning] = []

    for agent in AGENTS:
        agent_findings, agent_warnings = agent.analyze(request, tax_rule_context)
        findings.extend(agent_findings)
        warnings.extend(agent_warnings)

    deduped_warnings = _dedupe_warnings(warnings)
    next_questions = _next_questions_from_warnings(deduped_warnings)
    missing_information = _missing_information_from_warnings(deduped_warnings)

    return TaxAnalysisResponse(
        status=_response_status(deduped_warnings),
        findings=findings,
        warnings=deduped_warnings,
        next_questions=next_questions,
        missing_information=missing_information,
    )


def _load_tax_rule_context(request: TaxScenarioRequest) -> Any:
    tax_year = request.profile.tax_year
    if tax_year is None:
        return {
            "status": "error",
            "code": "MISSING_TAX_YEAR",
            "message": "Tax year is required before tax rule context can be loaded.",
        }

    return get_tax_rule_context(
        tax_year=tax_year,
        state_code=request.profile.resident_state,
    )


def _dedupe_warnings(warnings: list[AgentWarning]) -> list[AgentWarning]:
    deduped: list[AgentWarning] = []
    seen: set[tuple[str, str]] = set()

    for warning in warnings:
        key = (warning.code, warning.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)

    return deduped


def _next_questions_from_warnings(warnings: list[AgentWarning]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for warning in warnings:
        question = warning.recommended_follow_up
        if not question or question in seen:
            continue
        seen.add(question)
        questions.append(question)

    return questions


def _missing_information_from_warnings(warnings: list[AgentWarning]) -> list[str]:
    missing_information: list[str] = []
    seen: set[str] = set()

    for warning in warnings:
        missing_item = MISSING_INFORMATION_BY_WARNING_CODE.get(warning.code)
        if not missing_item or missing_item in seen:
            continue
        seen.add(missing_item)
        missing_information.append(missing_item)

    return missing_information


def _response_status(warnings: list[AgentWarning]) -> str:
    if any(warning.code.startswith("MISSING_") for warning in warnings):
        return "needs_more_information"
    if warnings:
        return "review_required"
    return "draft"
