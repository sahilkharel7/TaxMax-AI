from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable

from app.schemas import (
    AgentWarning,
    TaxOptimizationResponse,
    TaxSavingsOpportunity,
    TaxScenarioRequest,
)
from app.services.gemini_agent_contracts import run_gemini_agent
from app.services.tax_rule_service import get_tax_rule_context


FINAL_STRATEGY_SYSTEM_PROMPT = """
You are TaxMax AI's Final Savings Strategy Agent.
Review only legal tax-saving opportunities for a U.S. tax preparation workflow.
Return JSON with keys: opportunities, next_questions, missing_information, notes.
Do not calculate final taxes, promise savings, guarantee refunds, or claim eligibility.
Use cautious language such as "may apply", "needs review", and "requires confirmation".
"""


IMPACT_ORDER = {"high": 0, "medium": 1, "low": 2, "unknown": 3}


def optimize_tax_scenario(request: TaxScenarioRequest) -> TaxOptimizationResponse:
    """Return legal tax-saving review opportunities with cautious wording."""

    tax_rule_context = get_tax_rule_context(
        tax_year=request.profile.tax_year or 2025,
        state_code=request.profile.resident_state,
    )
    tax_rule_payload = tax_rule_context.model_dump()

    opportunities: list[TaxSavingsOpportunity] = []
    warnings: list[AgentWarning] = []
    missing_information: list[str] = []
    next_questions: list[str] = []

    _baseline_missing_info(request, missing_information, next_questions, warnings)
    opportunities.extend(_deduction_opportunities(request, tax_rule_payload))
    opportunities.extend(_credit_opportunities(request, tax_rule_payload))
    opportunities.extend(_filing_status_opportunities(request))
    opportunities.extend(_state_opportunities(request, tax_rule_payload))
    opportunities.extend(_documentation_opportunities(request))

    gemini_result = run_gemini_agent(
        agent_name="Final Savings Strategy Agent",
        system_prompt=FINAL_STRATEGY_SYSTEM_PROMPT,
        scenario=request,
        tax_rule_context=tax_rule_payload,
    )
    if gemini_result is not None:
        opportunities.extend(gemini_result.opportunities)
        next_questions.extend(gemini_result.next_questions)
        missing_information.extend(gemini_result.missing_information)

    opportunities = _dedupe_opportunities(opportunities)
    opportunities.sort(key=lambda item: (IMPACT_ORDER[item.potential_impact], item.title))

    status = _status(opportunities, warnings, missing_information)
    return TaxOptimizationResponse(
        status=status,
        opportunities=opportunities,
        warnings=_dedupe_warnings(warnings),
        missing_information=_dedupe_strings(missing_information),
        next_questions=_dedupe_strings(next_questions),
        review_package_summary=_review_package_summary(opportunities, missing_information),
    )


def _baseline_missing_info(
    request: TaxScenarioRequest,
    missing: list[str],
    questions: list[str],
    warnings: list[AgentWarning],
) -> None:
    if request.profile.tax_year is None:
        missing.append("Tax year")
        questions.append("Which tax year should the savings review use?")
    if request.profile.filing_status is None:
        missing.append("Filing status")
        questions.append("Which filing status are you considering?")
    if request.profile.resident_state is None:
        missing.append("Resident state")
        questions.append("What was your resident state for the tax year?")
    if request.income is None and request.self_employment is None:
        missing.append("Income details")
        questions.append("Do you have W-2, 1099, self-employment, or other income to review?")
    if request.profile.can_be_claimed_as_dependent is None:
        missing.append("Dependency status")
        questions.append("Can another taxpayer claim you as a dependent?")
        warnings.append(
            AgentWarning(
                severity="medium",
                code="OPTIMIZATION_DEPENDENCY_UNKNOWN",
                message="Dependency status is needed before credit and education opportunities can be reviewed safely.",
                recommended_follow_up="Confirm whether another taxpayer can claim the user.",
            )
        )


def _deduction_opportunities(
    request: TaxScenarioRequest,
    tax_rule_context: dict[str, Any],
) -> list[TaxSavingsOpportunity]:
    opportunities: list[TaxSavingsOpportunity] = []
    itemized = request.itemized_deductions
    federal_sources = _source_references(tax_rule_context)

    if itemized and _any_money(
        itemized.mortgage_interest,
        itemized.property_taxes,
        itemized.state_local_taxes_paid,
        itemized.charitable_cash,
        itemized.charitable_non_cash,
        itemized.medical_expenses,
    ):
        opportunities.append(
            _opportunity(
                opportunity_id="deduction_itemized_review",
                agent_name="Deduction Discovery Agent",
                category="deduction",
                title="Compare standard vs itemized deductions",
                summary="Itemized deduction inputs are present, so comparing them with the standard deduction may be worth reviewing.",
                potential_impact="medium",
                confidence="medium",
                required_facts=["Confirmed filing status", "Adjusted gross income", "Whether any dependent standard deduction limits apply"],
                required_documents=["Mortgage interest statement", "Property tax records", "Charitable receipts", "Medical expense records where relevant"],
                estimated_directional_effect="May reduce taxable income if allowable itemized deductions exceed the applicable standard deduction.",
                risk_level="medium",
                risk_notes=["Itemized deductions require source documentation and may differ between federal and state returns."],
                suggested_next_step="Collect itemized deduction records and compare them with the verified standard deduction during professional review.",
                source_references=federal_sources,
            )
        )

    if request.education and request.education.student_loan_interest is not None:
        opportunities.append(
            _opportunity(
                opportunity_id="deduction_student_loan_interest",
                agent_name="Deduction Discovery Agent",
                category="education",
                title="Review student loan interest deduction",
                summary="Student loan interest was provided and may support a deduction review if income and loan facts are confirmed.",
                potential_impact="low",
                confidence="medium",
                required_facts=["Modified AGI", "Filing status", "Whether the loan was a qualified student loan"],
                required_documents=["Form 1098-E or lender interest statement"],
                estimated_directional_effect="May reduce taxable income, subject to limits and phaseout rules.",
                risk_level="low",
                risk_notes=["Income phaseouts and qualified-loan facts must be verified."],
                suggested_next_step="Confirm Form 1098-E and review the deduction limits with a qualified tax professional.",
                source_references=federal_sources,
            )
        )

    se = request.self_employment
    if se or (request.income and request.income.self_employment_income is not None):
        opportunities.append(
            _opportunity(
                opportunity_id="deduction_self_employment_expenses",
                agent_name="Deduction Discovery Agent",
                category="self_employment",
                title="Review self-employment expense documentation",
                summary="Self-employment income is present, so ordinary and necessary business expenses may need review.",
                potential_impact="high",
                confidence="medium",
                required_facts=["Gross business income", "Expense categories", "Estimated payments", "Business use percentages where relevant"],
                required_documents=["1099-NEC or income records", "Receipts", "Mileage log", "Home office records if applicable"],
                estimated_directional_effect="May reduce net self-employment income if expenses are allowable and documented.",
                risk_level="medium",
                risk_notes=["Self-employment deductions need strong records and may affect self-employment tax."],
                suggested_next_step="Organize income, receipts, mileage, and home office records before professional review.",
                source_references=federal_sources,
            )
        )

    retirement = request.retirement
    if retirement and (
        retirement.traditional_ira_contribution is not None
        or retirement.employer_plan_contribution is not None
        or retirement.has_employer_retirement_plan is not None
    ):
        opportunities.append(
            _opportunity(
                opportunity_id="deduction_retirement_contributions",
                agent_name="Deduction Discovery Agent",
                category="retirement",
                title="Review retirement contribution opportunities",
                summary="Retirement contribution facts are present, so IRA, employer-plan, and saver-related review may be relevant.",
                potential_impact="medium",
                confidence="medium",
                required_facts=["Earned income", "Age", "Employer plan coverage", "Contribution dates and amounts"],
                required_documents=["IRA contribution records", "W-2 Box 12", "Plan statements"],
                estimated_directional_effect="May reduce taxable income or surface a credit review, depending on contribution type and income.",
                risk_level="medium",
                risk_notes=["Deductibility and credit treatment depend on income, plan coverage, age, and filing status."],
                suggested_next_step="Confirm contribution amounts and plan coverage before deciding how to report retirement items.",
                source_references=federal_sources,
            )
        )

    hsa = request.hsa
    if hsa and (hsa.had_hdhp_coverage or hsa.hsa_contribution is not None):
        opportunities.append(
            _opportunity(
                opportunity_id="deduction_hsa_contribution",
                agent_name="Deduction Discovery Agent",
                category="hsa",
                title="Review HSA contribution treatment",
                summary="HSA facts are present and may support review of contribution limits and reporting.",
                potential_impact="medium",
                confidence="medium",
                required_facts=["HDHP coverage months", "Coverage type", "Employer HSA contributions", "Taxpayer age"],
                required_documents=["Form 5498-SA", "Form 1099-SA if distributions occurred", "Employer HSA contribution records"],
                estimated_directional_effect="May reduce taxable income if eligible contributions are confirmed.",
                risk_level="medium",
                risk_notes=["HSA eligibility requires qualifying HDHP coverage and contribution limits must be checked."],
                suggested_next_step="Confirm HDHP coverage and total HSA contributions before reporting.",
                source_references=federal_sources,
            )
        )

    return opportunities


def _credit_opportunities(
    request: TaxScenarioRequest,
    tax_rule_context: dict[str, Any],
) -> list[TaxSavingsOpportunity]:
    opportunities: list[TaxSavingsOpportunity] = []
    sources = _source_references(tax_rule_context)
    dependent_count = request.profile.dependents_count or len(request.dependents)

    if request.profile.was_student or request.profile.received_1098_t or (
        request.education and (request.education.received_1098_t or request.education.qualified_expenses is not None)
    ):
        opportunities.append(
            _opportunity(
                opportunity_id="credit_education_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review education credits",
                summary="Student or 1098-T facts are present, so American Opportunity Credit or Lifetime Learning Credit review may apply.",
                potential_impact="medium",
                confidence="medium",
                required_facts=["Dependency status", "Qualified expenses", "Scholarships or grants", "Degree program and half-time status for AOTC"],
                required_documents=["Form 1098-T", "School account statement", "Course material receipts where relevant"],
                estimated_directional_effect="May reduce tax if credit requirements are confirmed.",
                risk_level="medium",
                risk_notes=["AOTC and LLC cannot both be claimed for the same student in the same year."],
                suggested_next_step="Confirm 1098-T details, dependency status, and student eligibility facts.",
                source_references=sources,
            )
        )

    if dependent_count > 0:
        opportunities.append(
            _opportunity(
                opportunity_id="credit_dependent_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review dependent-related credits",
                summary="Dependent information is present, so Child Tax Credit or Credit for Other Dependents review may be relevant.",
                potential_impact="high",
                confidence="medium",
                required_facts=["Dependent age", "Relationship", "Residency months", "Support test", "Valid SSN or tax ID"],
                required_documents=["Dependent SSN records", "School or residency records where relevant", "Custody/support documentation if needed"],
                estimated_directional_effect="May reduce tax if dependent credit requirements are confirmed.",
                risk_level="medium",
                risk_notes=["Dependent credits require exact dependent facts and identification details."],
                suggested_next_step="Collect dependent details before discussing credit treatment.",
                source_references=sources,
            )
        )

    income_amount = _income_amount(request)
    if income_amount is not None and income_amount <= Decimal("68675"):
        opportunities.append(
            _opportunity(
                opportunity_id="credit_eitc_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review Earned Income Tax Credit",
                summary="Earned income appears within a range where EITC review may be relevant, depending on filing status and qualifying children.",
                potential_impact="high" if dependent_count else "medium",
                confidence="low",
                required_facts=["Adjusted gross income", "Investment income", "Qualifying child facts", "Valid Social Security numbers"],
                required_documents=["W-2 or self-employment records", "Dependent records if applicable"],
                estimated_directional_effect="May create or increase a refundable credit if all EITC requirements are met.",
                risk_level="medium",
                risk_notes=["EITC has strict income, investment income, residency, relationship, and filing-status requirements."],
                suggested_next_step="Use confirmed income and dependent facts to review EITC with a qualified tax professional.",
                source_references=sources,
            )
        )

    if request.childcare and request.childcare.expenses is not None:
        opportunities.append(
            _opportunity(
                opportunity_id="credit_dependent_care_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review child and dependent care credit",
                summary="Dependent care expenses are present and may support a credit review if work-related care facts are confirmed.",
                potential_impact="medium",
                confidence="medium",
                required_facts=["Qualifying person facts", "Work-related care purpose", "Provider name, address, and tax ID"],
                required_documents=["Provider statement or receipts", "Dependent care records"],
                estimated_directional_effect="May reduce tax if care expense requirements are met.",
                risk_level="medium",
                risk_notes=["Provider identification and work-related purpose are important documentation points."],
                suggested_next_step="Confirm provider details and whether care allowed the taxpayer or spouse to work or look for work.",
                source_references=sources,
            )
        )

    if request.retirement and request.retirement.eligible_for_savers_credit_review:
        opportunities.append(
            _opportunity(
                opportunity_id="credit_savers_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review Saver's Credit",
                summary="Retirement contribution facts suggest Saver's Credit review may be useful for a low- or moderate-income taxpayer.",
                potential_impact="low",
                confidence="low",
                required_facts=["Adjusted gross income", "Retirement contribution amount", "Student and dependent status"],
                required_documents=["IRA or employer plan contribution records"],
                estimated_directional_effect="May reduce tax if income and contribution requirements are met.",
                risk_level="low",
                risk_notes=["Eligibility depends on income, filing status, age, student status, and dependent status."],
                suggested_next_step="Confirm retirement contributions and AGI before reviewing Saver's Credit.",
                source_references=sources,
            )
        )

    if request.clean_energy and (
        request.clean_energy.home_energy_improvements is not None
        or request.clean_energy.solar_or_battery_storage is not None
        or request.clean_energy.clean_vehicle_purchase
    ):
        opportunities.append(
            _opportunity(
                opportunity_id="credit_clean_energy_review",
                agent_name="Credit Discovery Agent",
                category="credit",
                title="Review clean energy or vehicle credits",
                summary="Clean energy or vehicle purchase signals are present, so credit review may be relevant if product, property, and documentation requirements are confirmed.",
                potential_impact="medium",
                confidence="low",
                required_facts=["Property placed-in-service date", "Product eligibility", "Income limits where applicable", "Seller report for vehicle credits"],
                required_documents=["Invoices", "Manufacturer certification where required", "Seller report for vehicle credits"],
                estimated_directional_effect="May reduce tax if statutory credit requirements are confirmed.",
                risk_level="high",
                risk_notes=["Clean energy and vehicle credits are documentation-heavy and rule-specific."],
                suggested_next_step="Gather invoices and eligibility documentation before professional review.",
                source_references=sources,
            )
        )

    return opportunities


def _filing_status_opportunities(request: TaxScenarioRequest) -> list[TaxSavingsOpportunity]:
    opportunities: list[TaxSavingsOpportunity] = []
    filing_status = request.profile.filing_status
    dependent_count = request.profile.dependents_count or len(request.dependents)

    if filing_status in {None, "single"} and dependent_count > 0:
        opportunities.append(
            _opportunity(
                opportunity_id="filing_status_head_of_household_review",
                agent_name="Filing Status Optimizer",
                category="filing_status",
                title="Review head-of-household possibility",
                summary="Dependent facts are present, so head-of-household review may be relevant if household support and qualifying-person rules are confirmed.",
                potential_impact="high",
                confidence="low",
                required_facts=["Marital status", "Qualifying person", "Months lived together", "Who paid more than half the home costs"],
                required_documents=["Dependent residency records", "Household expense records if needed"],
                estimated_directional_effect="May affect standard deduction and brackets if legally available.",
                risk_level="medium",
                risk_notes=["Filing status rules are fact-specific and should not be assumed from dependent count alone."],
                suggested_next_step="Confirm household support and qualifying-person facts before comparing filing statuses.",
            )
        )

    if filing_status in {"married_filing_jointly", "married_filing_separately"} or request.spouse:
        opportunities.append(
            _opportunity(
                opportunity_id="filing_status_mfj_mfs_review",
                agent_name="Filing Status Optimizer",
                category="filing_status",
                title="Compare MFJ vs MFS review factors",
                summary="Married filing facts are present, so comparing joint and separate filing considerations may be useful.",
                potential_impact="medium",
                confidence="low",
                required_facts=["Spouse income", "Student loan repayment facts", "Itemized deduction choice", "Community property state facts if applicable"],
                required_documents=["Spouse W-2 or income records", "Student loan records where relevant"],
                estimated_directional_effect="May affect deductions, credits, brackets, and repayment programs depending on facts.",
                risk_level="medium",
                risk_notes=["MFS can limit or disallow several credits and deductions; review carefully."],
                suggested_next_step="Gather spouse income and benefit facts before comparing filing approaches.",
            )
        )

    return opportunities


def _state_opportunities(
    request: TaxScenarioRequest,
    tax_rule_context: dict[str, Any],
) -> list[TaxSavingsOpportunity]:
    opportunities: list[TaxSavingsOpportunity] = []
    profile = request.profile
    state = profile.resident_state.upper() if profile.resident_state else None

    if not state:
        return opportunities

    opportunities.append(
        _opportunity(
            opportunity_id=f"state_{state.lower()}_review",
            agent_name="State Tax Optimization Agent",
            category="state_tax",
            title=f"Review {state} state tax opportunities",
            summary=f"{state} resident-state facts are present, so state-specific deductions, credits, and itemized deduction differences may be worth reviewing.",
            potential_impact="medium",
            confidence="medium",
            required_facts=["Resident state", "Work state", "State withholding", "State-specific deductions or credits"],
            required_documents=["State withholding forms", "State-specific credit or deduction documents"],
            estimated_directional_effect="May affect state taxable income or credits if state-specific rules apply.",
            risk_level="medium",
            risk_notes=["State rules can differ from federal rules and may require separate forms."],
            suggested_next_step="Review resident and work-state facts against state instructions before filing.",
            source_references=_source_references(tax_rule_context),
        )
    )

    if profile.work_state and state and profile.work_state.upper() != state:
        opportunities.append(
            _opportunity(
                opportunity_id="state_multistate_review",
                agent_name="State Tax Optimization Agent",
                category="state_tax",
                title="Review multi-state filing facts",
                summary="Resident and work states differ, so multi-state allocation and withholding review may apply.",
                potential_impact="high",
                confidence="medium",
                required_facts=["Residency dates", "Work location dates", "State wages", "State withholding"],
                required_documents=["W-2 state wage lines", "Residency records", "Employer work-location records"],
                estimated_directional_effect="May affect state filing requirements, credits for taxes paid, or allocation.",
                risk_level="high",
                risk_notes=["Multi-state returns are fact-specific and documentation-sensitive."],
                suggested_next_step="Confirm residency and work-state details before state filing decisions.",
                source_references=_source_references(tax_rule_context),
            )
        )

    return opportunities


def _documentation_opportunities(request: TaxScenarioRequest) -> list[TaxSavingsOpportunity]:
    opportunities: list[TaxSavingsOpportunity] = []
    needs_review_docs = [
        document
        for document in request.documents
        if document.extraction_status in {"needs_review", "error", "not_started"}
    ]
    if needs_review_docs:
        opportunities.append(
            _opportunity(
                opportunity_id="documentation_confirm_extracted_fields",
                agent_name="Risk Review Agent",
                category="documentation",
                title="Confirm document fields before claiming opportunities",
                summary="One or more documents still need review before extracted values are treated as reliable for savings analysis.",
                potential_impact="unknown",
                confidence="high",
                required_facts=["User-confirmed extracted values"],
                required_documents=[doc.file_name or doc.document_type for doc in needs_review_docs],
                estimated_directional_effect="Confirming documents can improve the reliability of deduction and credit review.",
                risk_level="high",
                risk_notes=["Unconfirmed extracted values can lead to incorrect review results."],
                suggested_next_step="Compare extracted fields against the original documents and confirm or correct them.",
            )
        )
    return opportunities


def _opportunity(**kwargs: Any) -> TaxSavingsOpportunity:
    kwargs.setdefault("professional_review_required", True)
    kwargs.setdefault("source_references", [])
    return TaxSavingsOpportunity(
        **kwargs,
    )


def _any_money(*values: Decimal | None) -> bool:
    return any(value is not None and value > 0 for value in values)


def _income_amount(request: TaxScenarioRequest) -> Decimal | None:
    values: list[Decimal] = []
    if request.income:
        for value in (
            request.income.w2_wages,
            request.income.self_employment_income,
            request.income.interest_income,
            request.income.other_income,
        ):
            if value is not None:
                values.append(value)
    if request.self_employment and request.self_employment.gross_income is not None:
        values.append(request.self_employment.gross_income)
    if not values:
        return None
    return sum(values, Decimal("0"))


def _source_references(tax_rule_context: dict[str, Any]) -> list[str]:
    refs = tax_rule_context.get("source_references", [])
    return [str(ref) for ref in refs] if isinstance(refs, list) else []


def _dedupe_opportunities(
    opportunities: Iterable[TaxSavingsOpportunity],
) -> list[TaxSavingsOpportunity]:
    deduped: list[TaxSavingsOpportunity] = []
    seen: set[str] = set()
    for opportunity in opportunities:
        if opportunity.opportunity_id in seen:
            continue
        seen.add(opportunity.opportunity_id)
        deduped.append(opportunity)
    return deduped


def _dedupe_warnings(warnings: Iterable[AgentWarning]) -> list[AgentWarning]:
    deduped: list[AgentWarning] = []
    seen: set[tuple[str, str]] = set()
    for warning in warnings:
        key = (warning.code, warning.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped


def _dedupe_strings(values: Iterable[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _status(
    opportunities: list[TaxSavingsOpportunity],
    warnings: list[AgentWarning],
    missing: list[str],
) -> str:
    if missing:
        return "needs_more_information"
    if warnings or any(item.risk_level in {"medium", "high"} for item in opportunities):
        return "review_required"
    return "draft"


def _review_package_summary(
    opportunities: list[TaxSavingsOpportunity],
    missing: list[str],
) -> str:
    if missing:
        return (
            "TaxMax AI found potential tax-savings review areas, but additional facts "
            "are needed before a professional can evaluate them."
        )
    if not opportunities:
        return (
            "TaxMax AI did not find specific savings opportunities from the supplied "
            "facts yet. Add income, deduction, credit, and document details for a deeper review."
        )
    return (
        f"TaxMax AI identified {len(opportunities)} potential legal tax-savings "
        "review opportunity area(s). Confirm facts and documentation with a qualified tax professional."
    )
