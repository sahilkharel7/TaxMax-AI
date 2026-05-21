from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent
from app.schemas import TaxScenarioRequest


class OptimizationAgent(BaseTaxAgent):
    """Suggests conservative planning review areas without calculating outcomes."""

    agent_name = "Optimization Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        if scenario.profile.multiple_jobs is True:
            findings.append(
                self.finding(
                    category="optimization",
                    summary="Withholding review may apply because multiple jobs are indicated.",
                    confidence="medium",
                    rationale="Multiple jobs can affect withholding assumptions, but this agent does not calculate tax due or refunds.",
                    suggested_action="Confirm all W-2 wages and withholding before reviewing possible withholding adjustments.",
                )
            )

        if scenario.income and scenario.income.self_employment_income is not None:
            findings.append(
                self.finding(
                    category="optimization",
                    summary="Estimated payment and recordkeeping review may apply for self-employment income.",
                    confidence="medium",
                    rationale="Self-employment income was supplied in the scenario.",
                    suggested_action="Ask for income records, expense records, and any estimated payment history.",
                )
            )

        if scenario.user_goal:
            findings.append(
                self.finding(
                    category="optimization",
                    summary="The user's stated goal can guide review, but recommendations require confirmed facts and verified rules.",
                    confidence="low",
                    rationale="A user goal was included with the scenario.",
                    suggested_action="Restate the goal as a review question and gather any missing documents before discussing scenarios.",
                )
            )
        else:
            warnings.append(
                self.warning(
                    code="MISSING_USER_GOAL",
                    message="The user's goal is missing, so optimization review needs direction.",
                    severity="low",
                    recommended_follow_up="Ask whether the user wants help with document review, missing information, withholding, credits, or filing readiness.",
                )
            )

        return findings, warnings
