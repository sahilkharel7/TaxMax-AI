"""Tax scenario analysis service.

Deterministic placeholder that produces a schema-valid `TaxAnalysisResponse`
from a supplied `TaxScenarioRequest`. The agent orchestrator (federal, state,
deduction, credit, optimization, risk, summary agents) will replace this
module while keeping `analyze_scenario` as the public entry point used by the
API layer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.schemas import (
    AgentFinding,
    AgentWarning,
    EducationInput,
    IncomeInput,
    ResponseStatus,
    TaxAnalysisResponse,
    TaxScenarioRequest,
    TaxpayerProfile,
)
from app.services.agent_orchestrator import analyze_tax_scenario
from app.services.tax_rule_service import (
    TaxRuleContext,
    TaxRuleError,
    get_tax_rule_context,
)


def analyze_scenario(request: TaxScenarioRequest) -> TaxAnalysisResponse:
    """Return a deterministic, schema-valid analysis response."""

    findings: list[AgentFinding] = []
    warnings: list[AgentWarning] = []
    next_questions: list[str] = []
    missing: list[str] = []

    _profile_signals(request.profile, warnings, next_questions, missing)
    _income_signals(request.income, findings, warnings, missing)
    _education_signals(
        request.profile, request.education, findings, warnings, next_questions, missing
    )
    _document_signals(request, findings, warnings)
    _rule_context_signals(request.profile, findings, warnings)

    orchestrated = analyze_tax_scenario(request)
    findings.extend(orchestrated.findings)
    warnings.extend(orchestrated.warnings)
    next_questions.extend(orchestrated.next_questions)
    missing.extend(orchestrated.missing_information)

    findings = _dedupe_findings(findings)
    warnings = _dedupe_warnings(warnings)
    next_questions = _dedupe_strings(next_questions)
    missing = _dedupe_strings(missing)

    if missing or any(w.severity == "high" for w in warnings):
        status: ResponseStatus = "needs_more_information"
    elif warnings:
        status = "review_required"
    else:
        status = "draft"

    return TaxAnalysisResponse(
        status=status,
        findings=findings,
        warnings=warnings,
        next_questions=next_questions,
        missing_information=missing,
    )


def _profile_signals(
    profile: TaxpayerProfile,
    warnings: list[AgentWarning],
    next_questions: list[str],
    missing: list[str],
) -> None:
    if profile.filing_status is None:
        missing.append("Filing status")
        next_questions.append("Which filing status applies to this return?")
    if profile.tax_year is None:
        missing.append("Tax year")
        next_questions.append("Which tax year should I review?")
    if profile.resident_state is None:
        missing.append("Resident state")
    if profile.can_be_claimed_as_dependent is None:
        warnings.append(
            AgentWarning(
                severity="medium",
                code="MISSING_DEPENDENCY_CONTEXT",
                message="Dependency status has not been confirmed.",
                recommended_follow_up=(
                    "Ask whether another taxpayer can claim the user as a dependent."
                ),
            )
        )
        next_questions.append(
            "Can another taxpayer claim you as a dependent for the tax year?"
        )


def _income_signals(
    income: Optional[IncomeInput],
    findings: list[AgentFinding],
    warnings: list[AgentWarning],
    missing: list[str],
) -> None:
    if income is None:
        missing.append("Income inputs")
        return

    if income.w2_wages is None and income.self_employment_income is None:
        warnings.append(
            AgentWarning(
                severity="medium",
                code="MISSING_INCOME_INPUTS",
                message="No wage or self-employment income has been provided.",
                recommended_follow_up=(
                    "Confirm whether the user had W-2 wages, 1099 income, or both."
                ),
            )
        )

    if income.w2_wages is not None and income.federal_withholding is None:
        warnings.append(
            AgentWarning(
                severity="low",
                code="MISSING_FEDERAL_WITHHOLDING",
                message="W-2 wages were provided without federal withholding.",
                recommended_follow_up="Confirm Box 2 (federal withholding) from each W-2.",
            )
        )

    if income.w2_wages is not None and income.w2_wages > Decimal("0"):
        findings.append(
            AgentFinding(
                agent_name="Income Agent",
                category="income",
                summary="W-2 wages were supplied and should be reviewed against the source W-2.",
                confidence="medium",
                rationale="W-2 wages were supplied via input or document extraction.",
                suggested_action=(
                    "Confirm Box 1, Box 2, and employer details before continuing."
                ),
            )
        )


def _education_signals(
    profile: TaxpayerProfile,
    education: Optional[EducationInput],
    findings: list[AgentFinding],
    warnings: list[AgentWarning],
    next_questions: list[str],
    missing: list[str],
) -> None:
    education_relevant = (
        profile.was_student is True
        or profile.received_1098_t is True
        or (education is not None and (education.is_student or education.received_1098_t))
    )

    if not education_relevant:
        return

    findings.append(
        AgentFinding(
            agent_name="Education Agent",
            category="education",
            summary=(
                "Education inputs appear relevant and should be reviewed alongside Form 1098-T details."
            ),
            confidence="medium",
            rationale=(
                "Student status or 1098-T receipt was indicated by the taxpayer."
            ),
            suggested_action=(
                "Confirm school, qualified expenses, scholarships, and dependency "
                "status before evaluating education-related options."
            ),
        )
    )

    if education is None or education.qualified_expenses is None:
        missing.append("Qualified education expenses")
        next_questions.append(
            "What qualified education expenses did you pay this tax year?"
        )

    if profile.can_be_claimed_as_dependent is None:
        warnings.append(
            AgentWarning(
                severity="medium",
                code="EDUCATION_DEPENDENCY_UNKNOWN",
                message=(
                    "Education review requires dependency context, which is not confirmed."
                ),
                recommended_follow_up=(
                    "Confirm whether another taxpayer can claim the user as a dependent."
                ),
            )
        )


def _document_signals(
    request: TaxScenarioRequest,
    findings: list[AgentFinding],
    warnings: list[AgentWarning],
) -> None:
    for document in request.documents:
        if document.extraction_status == "needs_review":
            findings.append(
                AgentFinding(
                    agent_name="Document Agent",
                    category="documents",
                    summary=(
                        f"Document {document.file_name or document.document_id or document.document_type} "
                        "has extracted fields that need user review."
                    ),
                    confidence="low",
                    rationale=(
                        "Extraction status was flagged as needs_review; values were not user-confirmed."
                    ),
                    suggested_action="Verify each extracted field against the source document.",
                    supporting_documents=[document.document_id or document.document_type],
                )
            )
        elif document.extraction_status == "error":
            warnings.append(
                AgentWarning(
                    severity="high",
                    code="DOCUMENT_EXTRACTION_ERROR",
                    message=(
                        f"Extraction error for document "
                        f"{document.file_name or document.document_id or document.document_type}."
                    ),
                    recommended_follow_up=(
                        "Ask the user to re-upload the document or enter values manually."
                    ),
                )
            )


def _rule_context_signals(
    profile: TaxpayerProfile,
    findings: list[AgentFinding],
    warnings: list[AgentWarning],
) -> None:
    if profile.tax_year is None:
        return

    rule_context = get_tax_rule_context(
        tax_year=profile.tax_year,
        state_code=profile.resident_state,
    )

    if isinstance(rule_context, TaxRuleError):
        warnings.append(
            AgentWarning(
                severity="medium",
                code=rule_context.code,
                message=rule_context.message,
                recommended_follow_up=(
                    "Verify supported tax years and states with the rule data team."
                ),
            )
        )
        return

    assert isinstance(rule_context, TaxRuleContext)
    findings.append(
        AgentFinding(
            agent_name="Rule Context Agent",
            category="rules",
            summary=(
                f"Loaded federal tax rule context for {rule_context.tax_year}"
                + (f" with state {rule_context.state_code}" if rule_context.state_code else "")
                + "."
            ),
            confidence="low",
            rationale=(
                "Federal and state rule files are placeholders pending verified data; "
                "agents must not rely on them for calculations yet."
            ),
            suggested_action=(
                "Replace placeholder rule data with verified IRS and state sources before final review."
            ),
        )
    )


def _dedupe_findings(findings: list[AgentFinding]) -> list[AgentFinding]:
    deduped: list[AgentFinding] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.agent_name, finding.category, finding.summary)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


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


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
