from app.services.tax_rule_service import (
    TaxRuleContext,
    TaxRuleError,
    get_tax_rule_context,
    get_tax_rule_context_dict,
)


def test_loads_federal_and_state_rule_context() -> None:
    context = get_tax_rule_context(2025, "ca")

    assert isinstance(context, TaxRuleContext)
    assert context.status == "ok"
    assert context.tax_year == 2025
    assert context.federal["jurisdiction"] == "US"
    assert context.state_code == "CA"
    assert context.state is not None
    assert context.state["jurisdiction"] == "CA"
    assert context.source_references
    assert context.last_reviewed == {
        "federal": "2026-05-21",
        "state": "2026-05-21",
    }


def test_missing_rule_file_returns_controlled_error() -> None:
    context = get_tax_rule_context(2024, "NY")

    assert isinstance(context, TaxRuleError)
    assert context.status == "error"
    assert context.code == "TAX_RULE_FILE_MISSING"
    assert context.rule_scope == "federal"
    assert context.tax_year == 2024


def test_rule_context_can_be_returned_as_dictionary() -> None:
    context = get_tax_rule_context_dict(2025, "ny")

    assert context["status"] == "ok"
    assert context["state_code"] == "NY"
    assert context["state"]["jurisdiction"] == "NY"
