"""AI agent modules for TaxMax AI."""

from app.agents.credit_agent import CreditAgent
from app.agents.deduction_agent import DeductionAgent
from app.agents.federal_tax_agent import FederalTaxAgent
from app.agents.optimization_agent import OptimizationAgent
from app.agents.risk_review_agent import RiskReviewAgent
from app.agents.state_tax_agent import StateTaxAgent
from app.agents.summary_agent import SummaryAgent

__all__ = [
    "CreditAgent",
    "DeductionAgent",
    "FederalTaxAgent",
    "OptimizationAgent",
    "RiskReviewAgent",
    "StateTaxAgent",
    "SummaryAgent",
]
