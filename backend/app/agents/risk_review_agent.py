from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent
from app.schemas import TaxScenarioRequest


class RiskReviewAgent(BaseTaxAgent):
    """Flags incomplete or uncertain inputs for cautious review."""

    agent_name = "Risk Review Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        if scenario.profile.can_be_claimed_as_dependent is None:
            warnings.append(
                self.warning(
                    code="MISSING_DEPENDENT_STATUS",
                    message="Dependent status is unknown and requires confirmation before credit or education review.",
                    severity="medium",
                    recommended_follow_up="Ask whether another taxpayer can claim the user as a dependent.",
                )
            )

        if scenario.profile.filing_status is None:
            warnings.append(
                self.warning(
                    code="MISSING_FILING_STATUS",
                    message="Filing status is unknown and needs review before the scenario is summarized.",
                    severity="medium",
                    recommended_follow_up="Ask the user to choose the filing status they expect to use.",
                )
            )

        for document in scenario.documents:
            if document.extraction_status in {"needs_review", "error"}:
                warnings.append(
                    self.warning(
                        code="DOCUMENT_EXTRACTION_NEEDS_REVIEW",
                        message=f"{document.file_name or 'A document'} needs review before its fields are treated as confirmed.",
                        severity="medium",
                        recommended_follow_up="Ask the user to confirm extracted fields or upload a clearer document.",
                    )
                )

        if not warnings:
            findings.append(
                self.finding(
                    category="risk",
                    summary="No deterministic risk flags were triggered, but the scenario still requires professional review before filing.",
                    confidence="low",
                    rationale="This first agent version only checks a small set of missing or uncertain inputs.",
                    suggested_action="Continue collecting and confirming documents before preparing filing-ready outputs.",
                )
            )

        return findings, warnings
