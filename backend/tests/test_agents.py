from app.agents.credit_agent import CreditAgent
from app.agents.deduction_agent import DeductionAgent
from app.agents.federal_tax_agent import FederalTaxAgent
from app.agents.optimization_agent import OptimizationAgent
from app.agents.risk_review_agent import RiskReviewAgent
from app.agents.state_tax_agent import StateTaxAgent
from app.agents.summary_agent import SummaryAgent
from app.schemas import (
    AgentFinding,
    AgentWarning,
    EducationInput,
    TaxScenarioRequest,
    TaxpayerProfile,
)
from app.services.tax_rule_service import TaxRuleContext, get_tax_rule_context, get_tax_rule_context_dict


def test_credit_agent_flags_education_credit_review_for_1098_t() -> None:
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(tax_year=2025, received_1098_t=True),
        education=EducationInput(received_1098_t=True),
    )

    findings, warnings = CreditAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025),
    )

    assert any("may apply" in finding.summary for finding in findings)
    assert any(finding.category == "credits" for finding in findings)
    assert any(warning.code == "MISSING_DEPENDENCY_CONTEXT" for warning in warnings)


def test_risk_review_agent_warns_when_dependent_status_unknown() -> None:
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(tax_year=2025, filing_status="single"),
    )

    findings, warnings = RiskReviewAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025),
    )

    assert findings == []
    assert any(warning.code == "MISSING_DEPENDENT_STATUS" for warning in warnings)
    assert any("requires confirmation" in warning.message for warning in warnings)


def test_state_tax_agent_asks_for_missing_resident_state() -> None:
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(tax_year=2025, filing_status="single"),
    )

    findings, warnings = StateTaxAgent().analyze(
        scenario,
        get_tax_rule_context_dict(2025),
    )

    assert findings == []
    assert any(warning.code == "MISSING_RESIDENT_STATE" for warning in warnings)
    assert any("Ask the user for their resident state" in str(warning.recommended_follow_up) for warning in warnings)


def test_all_agents_return_findings_and_warnings_lists() -> None:
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="CA",
            can_be_claimed_as_dependent=False,
        ),
        education=EducationInput(received_1098_t=True),
    )
    tax_rule_context = get_tax_rule_context_dict(2025, "CA")
    agents = [
        FederalTaxAgent(),
        StateTaxAgent(),
        DeductionAgent(),
        CreditAgent(),
        OptimizationAgent(),
        RiskReviewAgent(),
        SummaryAgent(),
    ]

    for agent in agents:
        findings, warnings = agent.analyze(scenario, tax_rule_context)

        assert isinstance(findings, list)
        assert isinstance(warnings, list)
        assert all(isinstance(finding, AgentFinding) for finding in findings)
        assert all(isinstance(warning, AgentWarning) for warning in warnings)


def test_agents_accept_tax_rule_context_object() -> None:
    scenario = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="NY",
        ),
    )
    tax_rule_context = get_tax_rule_context(2025, "NY")

    assert isinstance(tax_rule_context, TaxRuleContext)
    findings, warnings = StateTaxAgent().analyze(scenario, tax_rule_context)

    assert warnings == []
    assert any(finding.category == "state" for finding in findings)
