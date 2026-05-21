from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas import TaxSavingsOpportunity, TaxScenarioRequest
from app.services.gemini_client import (
    GeminiNotConfiguredError,
    generate_structured_agent_response,
)


AGENT_JSON_GUARDRAILS = [
    "Return only valid JSON.",
    "Do not calculate final taxes.",
    "Do not estimate a final refund or final amount owed.",
    "Do not make final eligibility claims.",
    "Use cautious wording: may apply, needs review, requires confirmation.",
    "Include missing facts, required documents, and risk notes.",
    "Recommend qualified professional review before filing decisions.",
]


class AgentRunContext(BaseModel):
    """Sanitized context shared with Gemini-backed agents."""

    agent_name: str
    scenario: dict[str, Any]
    tax_rule_context: dict[str, Any]
    guardrails: list[str] = Field(default_factory=lambda: AGENT_JSON_GUARDRAILS.copy())


class GeminiAgentResult(BaseModel):
    """Validated structured result shape for savings-focused agents."""

    opportunities: list[TaxSavingsOpportunity] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def sanitized_scenario_payload(scenario: TaxScenarioRequest) -> dict[str, Any]:
    """Drop direct identifiers before optional model calls."""

    data = scenario.model_dump(mode="json")
    for key in ("ssn", "social_security_number", "address", "email"):
        data.pop(key, None)
    for document in data.get("documents", []):
        if isinstance(document, dict):
            document.pop("extracted_fields", None)
            document.pop("confirmed_fields", None)
    return data


def run_gemini_agent(
    *,
    agent_name: str,
    system_prompt: str,
    scenario: TaxScenarioRequest,
    tax_rule_context: dict[str, Any],
) -> GeminiAgentResult | None:
    """Run an optional Gemini-backed agent with strict fallback behavior."""

    payload = AgentRunContext(
        agent_name=agent_name,
        scenario=sanitized_scenario_payload(scenario),
        tax_rule_context=tax_rule_context,
    ).model_dump(mode="json")

    try:
        response = generate_structured_agent_response(
            system_prompt=system_prompt,
            user_payload=payload,
            response_schema_name="GeminiAgentResult",
        )
    except GeminiNotConfiguredError:
        return None

    if response.get("status") == "fallback":
        return None

    try:
        return GeminiAgentResult.model_validate(response)
    except Exception:
        return None
