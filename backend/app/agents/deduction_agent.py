from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent
from app.schemas import TaxScenarioRequest


class DeductionAgent(BaseTaxAgent):
    """Flags deduction areas for review without making eligibility claims."""

    agent_name = "Deduction Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        if scenario.profile.filing_status is None:
            warnings.append(
                self.warning(
                    code="MISSING_DEDUCTION_FILING_STATUS",
                    message="Filing status is missing and deduction review requires confirmation.",
                    recommended_follow_up="Ask for the user's expected filing status.",
                )
            )
        else:
            findings.append(
                self.finding(
                    category="deductions",
                    summary="Standard deduction review may apply based on filing status, but exact values require verified rules.",
                    confidence="low",
                    rationale="The placeholder rule files do not yet contain verified standard deduction details.",
                    suggested_action="Confirm filing status and use reviewed federal rules before comparing deduction options.",
                )
            )

        if scenario.income and scenario.income.self_employment_income is not None:
            findings.append(
                self.finding(
                    category="deductions",
                    summary="Self-employment related deduction review may apply and needs documentation review.",
                    confidence="medium",
                    rationale="The scenario includes self-employment income.",
                    suggested_action="Ask for business expense records and any contractor income forms before deeper review.",
                )
            )

        if scenario.self_employment is not None:
            findings.append(
                self.finding(
                    category="deductions",
                    summary="Self-employment expense review may apply because business income or expense facts are present.",
                    confidence="medium",
                    rationale="The scenario includes self-employment review fields.",
                    suggested_action="Collect receipts, mileage logs, home office facts, and 1099 records before reviewing business deductions.",
                )
            )

        if scenario.itemized_deductions is not None:
            itemized = scenario.itemized_deductions
            itemized_values = [
                itemized.mortgage_interest,
                itemized.property_taxes,
                itemized.state_local_taxes_paid,
                itemized.charitable_cash,
                itemized.charitable_non_cash,
                itemized.medical_expenses,
            ]
            if any(value is not None and value > 0 for value in itemized_values):
                findings.append(
                    self.finding(
                        category="deductions",
                        summary="Itemized deduction review may apply because itemized expense inputs are present.",
                        confidence="medium",
                        rationale="The scenario includes potential itemized deduction amounts.",
                        suggested_action="Compare documented itemized deductions with the applicable standard deduction before filing decisions.",
                    )
                )

        if scenario.retirement is not None:
            retirement = scenario.retirement
            if (
                retirement.traditional_ira_contribution is not None
                or retirement.employer_plan_contribution is not None
                or retirement.has_employer_retirement_plan is not None
            ):
                findings.append(
                    self.finding(
                        category="deductions",
                        summary="Retirement contribution review may apply and requires income, age, and plan coverage confirmation.",
                        confidence="medium",
                        rationale="The scenario includes retirement contribution facts.",
                        suggested_action="Confirm contribution amounts, dates, employer plan coverage, and income before reviewing deductibility.",
                    )
                )

        if scenario.hsa is not None and (
            scenario.hsa.had_hdhp_coverage or scenario.hsa.hsa_contribution is not None
        ):
            findings.append(
                self.finding(
                    category="deductions",
                    summary="HSA contribution review may apply if HDHP eligibility and contribution limits are confirmed.",
                    confidence="medium",
                    rationale="The scenario includes HSA facts.",
                    suggested_action="Confirm HDHP coverage months, HSA contributions, employer contributions, and any distributions.",
                )
            )

        if scenario.education and scenario.education.qualified_expenses is not None:
            findings.append(
                self.finding(
                    category="deductions",
                    summary="Education expense information is present and needs review for possible deduction or adjustment context.",
                    confidence="low",
                    rationale="The user supplied education expense information.",
                    suggested_action="Confirm Form 1098-T, scholarships, and dependency context before discussing possible treatment.",
                )
            )

        return findings, warnings
