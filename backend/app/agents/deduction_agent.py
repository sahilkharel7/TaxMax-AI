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
