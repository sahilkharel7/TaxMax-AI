from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent
from app.schemas import TaxScenarioRequest


class SummaryAgent(BaseTaxAgent):
    """Produces cautious high-level summary findings."""

    agent_name = "Summary Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

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

        if completed_inputs:
            findings.append(
                self.finding(
                    category="summary",
                    summary=f"Initial review context includes {', '.join(completed_inputs)} and still needs confirmation.",
                    confidence="medium",
                    rationale="The summary agent only reports which inputs are present; it does not calculate taxes or determine eligibility.",
                    suggested_action="Use this as a preparation checklist before running deeper review.",
                )
            )

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
