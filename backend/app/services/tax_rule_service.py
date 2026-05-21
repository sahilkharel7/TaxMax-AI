from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


TAX_RULES_DIR = Path(__file__).resolve().parents[1] / "tax_rules"


class TaxRuleError(BaseModel):
    """Controlled tax rule loading error suitable for API responses."""

    status: Literal["error"] = Field(
        default="error",
        description="Rule loading status for controlled failures.",
    )
    code: str = Field(description="Stable error code for frontend and API handling.")
    message: str = Field(description="Human-readable error message.")
    rule_scope: str = Field(description="Rule scope that failed, such as federal or state.")
    tax_year: int = Field(description="Tax year requested by the caller.")
    state_code: Optional[str] = Field(
        default=None,
        description="Two-letter state code when a state rule file was requested.",
    )


class TaxRuleContext(BaseModel):
    """Tax rules loaded for a federal or federal-plus-state review context."""

    status: Literal["ok"] = Field(description="Rule loading status.")
    tax_year: int = Field(description="Tax year for this rule context.")
    federal: dict[str, Any] = Field(description="Federal tax rule payload for the tax year.")
    state_code: Optional[str] = Field(
        default=None,
        description="Two-letter state code when state rules are included.",
    )
    state: Optional[dict[str, Any]] = Field(
        default=None,
        description="State tax rule payload for the requested state and tax year.",
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Source references aggregated from loaded rule files.",
    )
    last_reviewed: dict[str, str] = Field(
        default_factory=dict,
        description="Last reviewed dates keyed by rule scope.",
    )


def get_tax_rule_context(
    tax_year: int,
    state_code: Optional[str] = None,
) -> Union[TaxRuleContext, TaxRuleError]:
    """Load federal rules and optional state rules for a tax scenario.

    Missing or invalid rule files return TaxRuleError instead of leaking filesystem
    or JSON parser details to API callers.
    """

    federal_path = _federal_rule_path(tax_year)
    federal_rules, federal_error = _load_rule_file(
        federal_path,
        rule_scope="federal",
        tax_year=tax_year,
    )
    if federal_error is not None:
        return federal_error

    state_rules: Optional[dict[str, Any]] = None
    normalized_state_code: Optional[str] = None
    if state_code:
        normalized_state_code = state_code.upper()
        state_path = _state_rule_path(normalized_state_code, tax_year)
        state_rules, state_error = _load_rule_file(
            state_path,
            rule_scope="state",
            tax_year=tax_year,
            state_code=normalized_state_code,
        )
        if state_error is not None:
            return state_error

    source_references = _source_references(federal_rules)
    last_reviewed = {"federal": str(federal_rules.get("last_reviewed", ""))}

    if state_rules is not None:
        source_references.extend(_source_references(state_rules))
        last_reviewed["state"] = str(state_rules.get("last_reviewed", ""))

    return TaxRuleContext(
        status="ok",
        tax_year=tax_year,
        federal=federal_rules,
        state_code=normalized_state_code,
        state=state_rules,
        source_references=source_references,
        last_reviewed=last_reviewed,
    )


def get_tax_rule_context_dict(
    tax_year: int,
    state_code: Optional[str] = None,
) -> dict[str, Any]:
    """Return tax rule context or controlled error as a plain dictionary."""

    return get_tax_rule_context(tax_year=tax_year, state_code=state_code).model_dump()


def _load_rule_file(
    path: Path,
    *,
    rule_scope: str,
    tax_year: int,
    state_code: str | None = None,
) -> tuple[dict[str, Any], Optional[TaxRuleError]]:
    if not path.exists():
        return {}, TaxRuleError(
            code="TAX_RULE_FILE_MISSING",
            message=f"No {rule_scope} tax rule file is available for tax year {tax_year}.",
            rule_scope=rule_scope,
            tax_year=tax_year,
            state_code=state_code,
        )

    try:
        with path.open("r", encoding="utf-8") as rule_file:
            return json.load(rule_file), None
    except json.JSONDecodeError:
        return {}, TaxRuleError(
            code="TAX_RULE_FILE_INVALID",
            message=f"The {rule_scope} tax rule file for tax year {tax_year} is not valid JSON.",
            rule_scope=rule_scope,
            tax_year=tax_year,
            state_code=state_code,
        )


def _federal_rule_path(tax_year: int) -> Path:
    return TAX_RULES_DIR / "federal" / f"{tax_year}.json"


def _state_rule_path(state_code: str, tax_year: int) -> Path:
    return TAX_RULES_DIR / "states" / state_code.upper() / f"{tax_year}.json"


def _source_references(rule_payload: dict[str, Any]) -> list[str]:
    references = rule_payload.get("source_references", [])
    if not isinstance(references, list):
        return []
    return [str(reference) for reference in references]
