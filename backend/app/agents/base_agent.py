from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import AgentFinding, AgentWarning, TaxScenarioRequest


AgentOutput = tuple[list[AgentFinding], list[AgentWarning]]


class BaseTaxAgent(ABC):
    """Base class for deterministic TaxMax AI tax review agents."""

    agent_name: str = "Base Tax Agent"

    @abstractmethod
    def analyze(
        self,
        scenario: TaxScenarioRequest,
        tax_rule_context: dict[str, Any],
    ) -> AgentOutput:
        """Return cautious findings and warnings for a tax scenario."""

    def finding(
        self,
        *,
        category: str,
        summary: str,
        confidence: str = "medium",
        rationale: str | None = None,
        suggested_action: str | None = None,
        supporting_documents: list[str] | None = None,
    ) -> AgentFinding:
        return AgentFinding(
            agent_name=self.agent_name,
            category=category,
            summary=summary,
            confidence=confidence,
            rationale=rationale,
            suggested_action=suggested_action,
            supporting_documents=supporting_documents or [],
        )

    def warning(
        self,
        *,
        code: str,
        message: str,
        severity: str = "medium",
        recommended_follow_up: str | None = None,
    ) -> AgentWarning:
        return AgentWarning(
            severity=severity,
            code=code,
            message=message,
            recommended_follow_up=recommended_follow_up,
        )


def rule_context_value(tax_rule_context: Any, key: str) -> Any:
    if isinstance(tax_rule_context, dict):
        return tax_rule_context.get(key)
    return getattr(tax_rule_context, key, None)


def rule_context_has_error(tax_rule_context: Any) -> bool:
    return rule_context_value(tax_rule_context, "status") == "error"


def source_ids_for_document_type(
    scenario: TaxScenarioRequest,
    document_type: str,
) -> list[str]:
    source_ids: list[str] = []
    for document in scenario.documents:
        if document.document_type == document_type and document.document_id:
            source_ids.append(document.document_id)
    return source_ids
