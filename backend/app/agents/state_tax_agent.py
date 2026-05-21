from __future__ import annotations

from typing import Any

from app.agents.base_agent import (
    AgentOutput,
    BaseTaxAgent,
    rule_context_has_error,
    rule_context_value,
)
from app.schemas import TaxScenarioRequest


class StateTaxAgent(BaseTaxAgent):
    """Reviews state context without calculating taxes."""

    agent_name = "State Tax Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        resident_state = scenario.profile.resident_state
        work_state = scenario.profile.work_state

        if resident_state is None:
            warnings.append(
                self.warning(
                    code="MISSING_RESIDENT_STATE",
                    message="Resident state is missing and state tax review requires confirmation.",
                    recommended_follow_up="Ask the user for their resident state for the tax year.",
                )
            )
            return findings, warnings

        if rule_context_has_error(tax_rule_context):
            warnings.append(
                self.warning(
                    code="STATE_RULE_CONTEXT_UNAVAILABLE",
                    message=f"State rule context for {resident_state.upper()} is unavailable and needs review.",
                    severity="high",
                    recommended_follow_up="Load a reviewed state rule file for the resident state and tax year.",
                )
            )
        elif rule_context_value(tax_rule_context, "state") is None:
            warnings.append(
                self.warning(
                    code="STATE_RULE_CONTEXT_NOT_LOADED",
                    message="Resident state is present, but no state rule context was loaded.",
                    recommended_follow_up="Load state rules using the confirmed resident state.",
                )
            )
        else:
            findings.append(
                self.finding(
                    category="state",
                    summary=f"{resident_state.upper()} state review may apply and requires confirmation against state-specific rules.",
                    confidence="medium",
                    rationale="A resident state and state rule context are available.",
                    suggested_action="Use the state rule context as a placeholder until verified rule details are added.",
                )
            )

        if work_state and work_state.upper() != resident_state.upper():
            findings.append(
                self.finding(
                    category="state",
                    summary="Multi-state review may apply because resident and work states differ.",
                    confidence="medium",
                    rationale="The user supplied different resident and work states.",
                    suggested_action="Confirm work location, residency dates, and any state withholding before discussing state treatment.",
                )
            )

        return findings, warnings
