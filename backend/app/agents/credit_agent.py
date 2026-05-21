from __future__ import annotations

from typing import Any

from app.agents.base_agent import AgentOutput, BaseTaxAgent, source_ids_for_document_type
from app.schemas import TaxScenarioRequest


class CreditAgent(BaseTaxAgent):
    """Flags credit areas for review without making eligibility claims."""

    agent_name = "Credit Agent"

    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        findings = []
        warnings = []

        has_1098_t = bool(
            scenario.education
            and scenario.education.received_1098_t is True
        ) or scenario.profile.received_1098_t is True

        if has_1098_t:
            findings.append(
                self.finding(
                    category="credits",
                    summary="Education credit review may apply because Form 1098-T information is present or expected.",
                    confidence="medium",
                    rationale="The scenario indicates a Form 1098-T.",
                    suggested_action="Confirm student status, dependency status, qualified expenses, scholarships, and institution details before discussing options.",
                    supporting_documents=source_ids_for_document_type(scenario, "1098_t"),
                )
            )
        elif scenario.education and scenario.education.is_student is True:
            warnings.append(
                self.warning(
                    code="MISSING_1098_T_CONFIRMATION",
                    message="Student status is present, but Form 1098-T status needs confirmation for education credit review.",
                    recommended_follow_up="Ask whether the user received Form 1098-T and whether the extracted fields are confirmed.",
                )
            )

        if scenario.profile.can_be_claimed_as_dependent is None:
            warnings.append(
                self.warning(
                    code="MISSING_DEPENDENCY_CONTEXT",
                    message="Dependency status is unknown and credit review requires confirmation.",
                    recommended_follow_up="Ask whether another taxpayer can claim the user as a dependent.",
                )
            )

        if scenario.profile.dependents_count is not None and scenario.profile.dependents_count > 0:
            findings.append(
                self.finding(
                    category="credits",
                    summary="Dependent-related credit review may apply and requires confirmation of dependent details.",
                    confidence="medium",
                    rationale="The scenario includes one or more dependents.",
                    suggested_action="Collect dependent ages, relationship, residency, support, and identification details before reviewing dependent-related credits.",
                )
            )

        if scenario.dependents:
            findings.append(
                self.finding(
                    category="credits",
                    summary="Dependent-related credit review may apply because dependent facts are present.",
                    confidence="medium",
                    rationale="The scenario includes dependent records.",
                    suggested_action="Confirm dependent age, relationship, residency, support, and identification details before reviewing credits.",
                )
            )

        if scenario.childcare and scenario.childcare.expenses is not None:
            findings.append(
                self.finding(
                    category="credits",
                    summary="Child and dependent care credit review may apply if work-related care and provider details are confirmed.",
                    confidence="medium",
                    rationale="The scenario includes dependent care expenses.",
                    suggested_action="Collect provider name, provider tax ID, receipts, and work-related care facts before reviewing the credit.",
                )
            )

        if scenario.retirement and scenario.retirement.eligible_for_savers_credit_review:
            findings.append(
                self.finding(
                    category="credits",
                    summary="Saver's Credit review may apply if income, age, student, dependent, and contribution facts are confirmed.",
                    confidence="low",
                    rationale="The scenario indicates Saver's Credit review interest.",
                    suggested_action="Confirm retirement contribution records and AGI before reviewing Saver's Credit.",
                )
            )

        if scenario.clean_energy and (
            scenario.clean_energy.home_energy_improvements is not None
            or scenario.clean_energy.solar_or_battery_storage is not None
            or scenario.clean_energy.clean_vehicle_purchase
        ):
            findings.append(
                self.finding(
                    category="credits",
                    summary="Clean energy or vehicle credit review may apply if product, property, income, and documentation requirements are confirmed.",
                    confidence="low",
                    rationale="The scenario includes clean energy or vehicle credit signals.",
                    suggested_action="Gather invoices, manufacturer or seller documentation, and placed-in-service details before reviewing credits.",
                )
            )

        return findings, warnings
