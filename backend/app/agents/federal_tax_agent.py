from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent, rule_context_has_error
from app.schemas import TaxScenarioRequest


class FederalTaxAgent(BaseTaxAgent):
    """Reviews federal context without calculating taxes."""

    agent_name = "Federal Tax Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        if rule_context_has_error(tax_rule_context):
            warnings.append(
                self.warning(
                    code="FEDERAL_RULE_CONTEXT_UNAVAILABLE",
                    message="Federal rule context is unavailable and needs review before federal guidance is expanded.",
                    severity="high",
                    recommended_follow_up="Load a reviewed federal rule file for the requested tax year.",
                )
            )
            return findings, warnings

        if scenario.profile.tax_year is None:
            warnings.append(
                self.warning(
                    code="MISSING_TAX_YEAR",
                    message="Tax year is missing, so federal review requires confirmation.",
                    recommended_follow_up="Ask the user which tax year should be reviewed.",
                )
            )

        if scenario.profile.filing_status is None:
            warnings.append(
                self.warning(
                    code="MISSING_FILING_STATUS",
                    message="Filing status is missing and may affect federal review.",
                    recommended_follow_up="Ask the user to confirm their expected filing status.",
                )
            )
        else:
            findings.append(
                self.finding(
                    category="federal",
                    summary="Federal filing status context is present and needs review against the full return facts.",
                    confidence="medium",
                    rationale="The user supplied a filing status, but this first agent version does not make final determinations.",
                    suggested_action="Use the filing status as review context only until all taxpayer details are confirmed.",
                )
            )

        if scenario.income is None:
            warnings.append(
                self.warning(
                    code="MISSING_INCOME_CONTEXT",
                    message="Income information is missing, so federal income review requires confirmation.",
                    recommended_follow_up="Ask for W-2, 1099, and other income details.",
                )
            )
        elif scenario.income.w2_wages is not None:
            findings.append(
                self.finding(
                    category="income",
                    summary="W-2 wage information is present and may be relevant for federal income review.",
                    confidence="medium",
                    rationale="The scenario includes W-2 wage input.",
                    suggested_action="Confirm extracted wages and withholding against the source document before deeper review.",
                )
            )

        return findings, warnings
