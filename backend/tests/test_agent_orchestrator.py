from app.schemas import EducationInput, TaxScenarioRequest, TaxpayerProfile
from app.services.agent_orchestrator import analyze_tax_scenario


def test_orchestrator_reports_missing_resident_state() -> None:
    request = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            can_be_claimed_as_dependent=False,
        ),
    )

    response = analyze_tax_scenario(request)

    assert response.status == "needs_more_information"
    assert "Resident state" in response.missing_information
    assert any(warning.code == "MISSING_RESIDENT_STATE" for warning in response.warnings)
    assert any("resident state" in question.lower() for question in response.next_questions)


def test_orchestrator_includes_1098_t_education_review() -> None:
    request = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="CA",
            can_be_claimed_as_dependent=False,
            received_1098_t=True,
        ),
        education=EducationInput(received_1098_t=True),
    )

    response = analyze_tax_scenario(request)

    assert any(finding.category == "credits" for finding in response.findings)
    assert any("Education credit review may apply" in finding.summary for finding in response.findings)
    assert "Dependency status" not in response.missing_information


def test_orchestrator_reports_and_dedupes_missing_dependent_status() -> None:
    request = TaxScenarioRequest(
        profile=TaxpayerProfile(
            tax_year=2025,
            filing_status="single",
            resident_state="NY",
            received_1098_t=True,
        ),
        education=EducationInput(received_1098_t=True),
    )

    response = analyze_tax_scenario(request)
    dependency_warnings = [
        warning
        for warning in response.warnings
        if warning.recommended_follow_up == "Ask whether another taxpayer can claim the user as a dependent."
    ]

    assert response.status == "needs_more_information"
    assert response.missing_information.count("Dependency status") == 1
    assert len(dependency_warnings) == 2
    assert (
        response.next_questions.count(
            "Ask whether another taxpayer can claim the user as a dependent."
        )
        == 1
    )
