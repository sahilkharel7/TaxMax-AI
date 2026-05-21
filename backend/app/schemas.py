from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


FilingStatus = Literal[
    "single",
    "married_filing_jointly",
    "married_filing_separately",
    "head_of_household",
    "qualifying_surviving_spouse",
]
ConfidenceLevel = Literal["low", "medium", "high"]
WarningSeverity = Literal["info", "low", "medium", "high"]
OpportunityImpact = Literal["low", "medium", "high", "unknown"]
RiskLevel = Literal["low", "medium", "high", "unknown"]
DocumentType = Literal[
    "w2",
    "1098_t",
    "1099_int",
    "1099_misc",
    "1099_nec",
    "other",
]
ResponseStatus = Literal[
    "draft",
    "needs_more_information",
    "review_required",
    "error",
]
OpportunityCategory = Literal[
    "deduction",
    "credit",
    "filing_status",
    "state_tax",
    "income",
    "retirement",
    "hsa",
    "education",
    "self_employment",
    "documentation",
    "risk",
    "general",
]


class HealthResponse(BaseModel):
    status: str = Field(description="Health status for the API service.")
    service: str = Field(description="Human-readable API service name.")
    ok: bool = Field(
        default=True,
        description="Boolean health flag for clients that prefer ok over status.",
    )
    provider: str = Field(
        default="gemini",
        description="LLM provider currently configured for agent responses.",
    )
    model: str = Field(
        default="",
        description="Configured LLM model name. Never includes any API key material.",
    )
    gemini_configured: bool = Field(
        default=False,
        alias="geminiConfigured",
        description=(
            "True when a server-side Gemini API key is present. The key itself is "
            "never returned by this endpoint."
        ),
    )

    model_config = ConfigDict(populate_by_name=True)


class TaxpayerProfile(BaseModel):
    """User-provided profile details that guide agent review."""

    filing_status: Optional[FilingStatus] = Field(
        default=None,
        description="User-selected filing status. Leave null when the user has not selected one.",
    )
    tax_year: Optional[int] = Field(
        default=None,
        ge=2000,
        le=2100,
        description="Tax year being reviewed, such as 2024.",
    )
    resident_state: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter resident state abbreviation, if known.",
        examples=["CA"],
    )
    work_state: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter work state abbreviation, if different or relevant.",
        examples=["NY"],
    )
    can_be_claimed_as_dependent: Optional[bool] = Field(
        default=None,
        description="Whether another taxpayer may be able to claim this taxpayer as a dependent.",
    )
    was_student: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer was a student during the tax year.",
    )
    received_1098_t: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer received Form 1098-T for education expenses.",
    )
    multiple_jobs: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer had more than one job during the tax year.",
    )
    received_1099: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer received any Form 1099 income documents.",
    )
    dependents_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of dependents entered by the user, if any.",
    )
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=125,
        description="Taxpayer age at the end of the tax year, if known.",
    )
    is_blind: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer is blind for standard deduction review.",
    )
    marital_status_known: Optional[bool] = Field(
        default=None,
        description="Whether marital status facts have been confirmed.",
    )
    paid_more_than_half_home_cost: Optional[bool] = Field(
        default=None,
        description="Potential head-of-household support fact; not a final determination.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filing_status": "single",
                "tax_year": 2024,
                "resident_state": "CA",
                "work_state": None,
                "can_be_claimed_as_dependent": False,
                "was_student": True,
                "received_1098_t": True,
                "multiple_jobs": False,
                "received_1099": False,
                "dependents_count": 0,
            }
        }
    )


class IncomeInput(BaseModel):
    """Income and withholding details supplied by the user or documents."""

    w2_wages: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Total W-2 wages entered or extracted from documents.",
    )
    federal_withholding: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Federal income tax withholding entered or extracted from documents.",
    )
    state_withholding: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="State income tax withholding entered or extracted from documents.",
    )
    interest_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Interest income from Form 1099-INT or manual entry.",
    )
    self_employment_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Self-employment or contractor income from manual entry or Form 1099.",
    )
    other_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Other income reported by the user for review context.",
    )
    unemployment_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Unemployment compensation, if known.",
    )
    dividend_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Dividend income from Form 1099-DIV or manual entry.",
    )
    capital_gain_income: Optional[Decimal] = Field(
        default=None,
        description="Capital gain or loss context supplied by the user.",
    )
    tip_income: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Tip income, including unreported tips where relevant.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "w2_wages": "64500.00",
                "federal_withholding": "7200.00",
                "state_withholding": "2100.00",
                "interest_income": "42.15",
                "self_employment_income": None,
                "other_income": None,
            }
        }
    )


class EducationInput(BaseModel):
    """Education-related facts used for documentation and question generation."""

    is_student: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer indicates they were a student.",
    )
    received_1098_t: Optional[bool] = Field(
        default=None,
        description="Whether the taxpayer has a Form 1098-T.",
    )
    qualified_expenses: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Education expenses supplied by the user for agent review.",
    )
    scholarships_or_grants: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Scholarships or grants that may affect education-related review.",
    )
    institution_name: Optional[str] = Field(
        default=None,
        description="Education institution name, if supplied by the user or document.",
    )
    student_loan_interest: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Student loan interest paid during the tax year, if known.",
    )
    pursuit_of_degree: Optional[bool] = Field(
        default=None,
        description="Whether the student pursued a degree or recognized credential.",
    )
    half_time_student: Optional[bool] = Field(
        default=None,
        description="Whether the student was enrolled at least half time.",
    )
    completed_first_four_years: Optional[bool] = Field(
        default=None,
        description="AOTC review fact: whether first four years of postsecondary education were completed before the tax year.",
    )
    felony_drug_conviction: Optional[bool] = Field(
        default=None,
        description="AOTC review fact; must be confirmed before eligibility discussion.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_student": True,
                "received_1098_t": True,
                "qualified_expenses": "3800.00",
                "scholarships_or_grants": "500.00",
                "institution_name": "Example State University",
            }
        }
    )


class DocumentInput(BaseModel):
    """Metadata and optional extraction output for an uploaded tax document."""

    document_id: Optional[str] = Field(
        default=None,
        description="Client or backend identifier for the uploaded document.",
    )
    document_type: DocumentType = Field(
        description="Type of tax document supplied by the user.",
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Original file name displayed to the user.",
    )
    extraction_status: Optional[
        Literal["not_started", "parsed", "needs_review", "error"]
    ] = Field(
        default=None,
        description="Current extraction status for this document.",
    )
    extracted_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Raw extracted field values for review; not treated as final tax facts.",
    )
    confirmed_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="User-confirmed extracted values. Agents may use these as reviewed facts but not final filing data.",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Uploaded file size for safety validation, if supplied by the client.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional user or system notes about this document.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "doc_w2_001",
                "document_type": "w2",
                "file_name": "2024-w2.pdf",
                "extraction_status": "needs_review",
                "extracted_fields": {
                    "employer_name": "Example Co",
                    "wages": "64500.00",
                    "federal_withholding": "7200.00",
                },
                "notes": "User should confirm extracted wage and withholding fields.",
            }
        }
    )


class SpouseProfile(BaseModel):
    """Optional spouse facts for married filing scenario review."""

    has_income: Optional[bool] = Field(
        default=None,
        description="Whether spouse has income that may affect MFJ/MFS review.",
    )
    w2_wages: Optional[Decimal] = Field(default=None, ge=0)
    federal_withholding: Optional[Decimal] = Field(default=None, ge=0)
    student_loan_plan: Optional[bool] = Field(
        default=None,
        description="Whether spouse student-loan repayment or benefit facts may affect MFS/MFJ planning.",
    )
    itemizes_separately: Optional[bool] = Field(
        default=None,
        description="Whether spouse would itemize if filing separately.",
    )


class DependentInput(BaseModel):
    """Dependent facts needed for cautious credit and filing-status review."""

    age: Optional[int] = Field(default=None, ge=0, le=125)
    relationship: Optional[str] = Field(default=None)
    months_lived_with_taxpayer: Optional[int] = Field(default=None, ge=0, le=12)
    provided_over_half_support: Optional[bool] = Field(default=None)
    has_valid_ssn: Optional[bool] = Field(default=None)
    was_student: Optional[bool] = Field(default=None)
    disabled: Optional[bool] = Field(default=None)
    childcare_expenses_paid: Optional[Decimal] = Field(default=None, ge=0)


class ItemizedDeductionsInput(BaseModel):
    """Potential itemized deduction facts for review."""

    mortgage_interest: Optional[Decimal] = Field(default=None, ge=0)
    property_taxes: Optional[Decimal] = Field(default=None, ge=0)
    state_local_taxes_paid: Optional[Decimal] = Field(default=None, ge=0)
    charitable_cash: Optional[Decimal] = Field(default=None, ge=0)
    charitable_non_cash: Optional[Decimal] = Field(default=None, ge=0)
    medical_expenses: Optional[Decimal] = Field(default=None, ge=0)
    gambling_losses: Optional[Decimal] = Field(default=None, ge=0)
    gambling_winnings: Optional[Decimal] = Field(default=None, ge=0)


class SelfEmploymentInput(BaseModel):
    """Self-employment facts used to find documentation and deduction review areas."""

    gross_income: Optional[Decimal] = Field(default=None, ge=0)
    expenses: Optional[Decimal] = Field(default=None, ge=0)
    home_office_used_regularly_exclusively: Optional[bool] = Field(default=None)
    business_miles: Optional[Decimal] = Field(default=None, ge=0)
    has_1099_nec: Optional[bool] = Field(default=None)
    made_estimated_payments: Optional[bool] = Field(default=None)


class RetirementInput(BaseModel):
    """Retirement contribution facts for saver, IRA, and deferral review."""

    traditional_ira_contribution: Optional[Decimal] = Field(default=None, ge=0)
    roth_ira_contribution: Optional[Decimal] = Field(default=None, ge=0)
    employer_plan_contribution: Optional[Decimal] = Field(default=None, ge=0)
    has_employer_retirement_plan: Optional[bool] = Field(default=None)
    eligible_for_savers_credit_review: Optional[bool] = Field(default=None)


class HsaInput(BaseModel):
    """HSA facts for contribution and documentation review."""

    had_hdhp_coverage: Optional[bool] = Field(default=None)
    coverage_type: Optional[Literal["self_only", "family"]] = Field(default=None)
    hsa_contribution: Optional[Decimal] = Field(default=None, ge=0)
    employer_hsa_contribution: Optional[Decimal] = Field(default=None, ge=0)


class ChildcareInput(BaseModel):
    """Dependent care facts for credit review."""

    expenses: Optional[Decimal] = Field(default=None, ge=0)
    care_provider_name_present: Optional[bool] = Field(default=None)
    care_provider_tax_id_present: Optional[bool] = Field(default=None)
    work_related: Optional[bool] = Field(default=None)


class CleanEnergyInput(BaseModel):
    """Clean energy and vehicle signals for cautious credit review."""

    home_energy_improvements: Optional[Decimal] = Field(default=None, ge=0)
    solar_or_battery_storage: Optional[Decimal] = Field(default=None, ge=0)
    clean_vehicle_purchase: Optional[bool] = Field(default=None)
    vehicle_make_model_year_present: Optional[bool] = Field(default=None)
    seller_report_available: Optional[bool] = Field(default=None)


class TaxSavingsPreferences(BaseModel):
    """User goal metadata for ranking opportunities."""

    priority: Optional[
        Literal[
            "maximize_refund_review",
            "reduce_taxable_income",
            "find_missing_documents",
            "compare_filing_options",
            "general_review",
        ]
    ] = Field(default="general_review")
    risk_tolerance: Optional[Literal["low", "medium", "high"]] = Field(default="low")
    wants_state_review: Optional[bool] = Field(default=True)


class TaxScenarioRequest(BaseModel):
    """Structured input for an AI-assisted tax scenario review."""

    profile: TaxpayerProfile = Field(
        description="Taxpayer profile answers supplied by the user.",
    )
    income: Optional[IncomeInput] = Field(
        default=None,
        description="Income and withholding inputs available for review.",
    )
    education: Optional[EducationInput] = Field(
        default=None,
        description="Education-related inputs available for review.",
    )
    spouse: Optional[SpouseProfile] = Field(
        default=None,
        description="Spouse facts for cautious filing-status comparison.",
    )
    dependents: list[DependentInput] = Field(
        default_factory=list,
        description="Dependent facts used for credit and filing-status review.",
    )
    itemized_deductions: Optional[ItemizedDeductionsInput] = Field(
        default=None,
        description="Potential itemized deduction inputs.",
    )
    self_employment: Optional[SelfEmploymentInput] = Field(
        default=None,
        description="Self-employment facts and expense signals.",
    )
    retirement: Optional[RetirementInput] = Field(
        default=None,
        description="Retirement contribution facts for legal savings review.",
    )
    hsa: Optional[HsaInput] = Field(
        default=None,
        description="Health Savings Account facts for contribution review.",
    )
    childcare: Optional[ChildcareInput] = Field(
        default=None,
        description="Dependent care expense facts for credit review.",
    )
    clean_energy: Optional[CleanEnergyInput] = Field(
        default=None,
        description="Clean energy and vehicle credit signals.",
    )
    documents: list[DocumentInput] = Field(
        default_factory=list,
        description="Uploaded or parsed tax documents available to the agent workflow.",
    )
    tax_savings_preferences: Optional[TaxSavingsPreferences] = Field(
        default=None,
        description="User preferences for ranking review opportunities.",
    )
    user_goal: Optional[str] = Field(
        default=None,
        description="Optional user goal or question for the analysis request.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile": {
                    "filing_status": "single",
                    "tax_year": 2024,
                    "resident_state": "CA",
                    "work_state": None,
                    "can_be_claimed_as_dependent": False,
                    "was_student": True,
                    "received_1098_t": True,
                    "multiple_jobs": False,
                    "received_1099": False,
                    "dependents_count": 0,
                },
                "income": {
                    "w2_wages": "64500.00",
                    "federal_withholding": "7200.00",
                    "state_withholding": "2100.00",
                    "interest_income": "42.15",
                    "self_employment_income": None,
                    "other_income": None,
                },
                "education": {
                    "is_student": True,
                    "received_1098_t": True,
                    "qualified_expenses": "3800.00",
                    "scholarships_or_grants": "500.00",
                    "institution_name": "Example State University",
                },
                "documents": [
                    {
                        "document_id": "doc_w2_001",
                        "document_type": "w2",
                        "file_name": "2024-w2.pdf",
                        "extraction_status": "needs_review",
                        "extracted_fields": {
                            "wages": "64500.00",
                            "federal_withholding": "7200.00",
                        },
                        "notes": None,
                    }
                ],
                "user_goal": "Review my uploaded documents and tell me what is missing.",
            }
        }
    )


class AgentFinding(BaseModel):
    """A non-final agent observation that may require user or preparer review."""

    agent_name: str = Field(
        description="Name of the agent or workflow step that produced the finding.",
        examples=["Credit Agent"],
    )
    category: str = Field(
        description="Topic category for the finding, such as income, education, deduction, or state.",
    )
    summary: str = Field(
        description="Plain-language summary of the observation without making final eligibility claims.",
    )
    confidence: ConfidenceLevel = Field(
        description="Agent confidence in this observation based on available information.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Brief explanation of why this finding was raised.",
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description="Suggested next action, framed as review guidance rather than a tax determination.",
    )
    supporting_documents: list[str] = Field(
        default_factory=list,
        description="Document identifiers or labels that support this observation.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_name": "Education Agent",
                "category": "education",
                "summary": "Education inputs appear relevant and should be reviewed with Form 1098-T details.",
                "confidence": "medium",
                "rationale": "The taxpayer marked student status and supplied education expenses.",
                "suggested_action": "Confirm school, expense, scholarship, and dependency details before evaluating education-related options.",
                "supporting_documents": ["doc_1098t_001"],
            }
        }
    )


class AgentWarning(BaseModel):
    """A risk, uncertainty, or documentation gap identified by an agent."""

    severity: WarningSeverity = Field(
        description="Severity level for the warning.",
    )
    code: str = Field(
        description="Stable warning code suitable for frontend handling.",
        examples=["MISSING_1098_T"],
    )
    message: str = Field(
        description="Plain-language warning message for the user.",
    )
    recommended_follow_up: Optional[str] = Field(
        default=None,
        description="Suggested follow-up question or document request.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "medium",
                "code": "MISSING_DEPENDENCY_CONTEXT",
                "message": "Dependency information is incomplete for education-related review.",
                "recommended_follow_up": "Ask whether another taxpayer can claim the user as a dependent.",
            }
        }
    )


class TaxSavingsOpportunity(BaseModel):
    """Legal tax-saving review opportunity returned by optimization agents."""

    opportunity_id: str = Field(description="Stable identifier for this opportunity.")
    agent_name: str = Field(description="Agent that raised the opportunity.")
    category: OpportunityCategory = Field(description="Opportunity category.")
    title: str = Field(description="Short user-facing title.")
    summary: str = Field(
        description="Cautious plain-language explanation without final claims.",
    )
    potential_impact: OpportunityImpact = Field(
        description="Directional impact only; not a final tax calculation.",
    )
    confidence: ConfidenceLevel = Field(description="Confidence based on supplied facts.")
    required_facts: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    estimated_directional_effect: Optional[str] = Field(
        default=None,
        description="Non-numeric description of possible tax direction.",
    )
    risk_level: RiskLevel = Field(description="Review risk level.")
    risk_notes: list[str] = Field(default_factory=list)
    suggested_next_step: str = Field(
        description="Next action framed as review guidance, not a tax instruction.",
    )
    professional_review_required: bool = Field(default=True)
    source_references: list[str] = Field(default_factory=list)


class TaxAnalysisResponse(BaseModel):
    """Validated agent response for tax scenario review."""

    status: ResponseStatus = Field(
        description="Overall response status for the analysis workflow.",
    )
    findings: list[AgentFinding] = Field(
        default_factory=list,
        description="Non-final observations generated by agent workflow steps.",
    )
    warnings: list[AgentWarning] = Field(
        default_factory=list,
        description="Warnings, uncertainty flags, and risk signals from the workflow.",
    )
    next_questions: list[str] = Field(
        default_factory=list,
        description="Questions the assistant should ask before deeper analysis.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Specific information or documents still needed from the user.",
    )
    disclaimer: str = Field(
        default=(
            "TaxMax AI provides AI-assisted preparation support and does not provide legal, "
            "tax, or financial advice. Review all information with a qualified professional "
            "before filing."
        ),
        description="Required user-facing disclaimer for analysis responses.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "needs_more_information",
                "findings": [
                    {
                        "agent_name": "Education Agent",
                        "category": "education",
                        "summary": "Education inputs may need additional document review before options can be discussed.",
                        "confidence": "medium",
                        "rationale": "Student status and education expenses were provided, but dependency context needs confirmation.",
                        "suggested_action": "Collect Form 1098-T and confirm whether another taxpayer can claim the user.",
                        "supporting_documents": ["doc_1098t_001"],
                    }
                ],
                "warnings": [
                    {
                        "severity": "medium",
                        "code": "MISSING_DEPENDENCY_CONTEXT",
                        "message": "Dependency information is incomplete.",
                        "recommended_follow_up": "Confirm whether another taxpayer can claim the user as a dependent.",
                    }
                ],
                "next_questions": [
                    "Can another taxpayer claim you as a dependent for the tax year?",
                    "Do you have the final Form 1098-T from your school?",
                ],
                "missing_information": ["Dependency status", "Confirmed 1098-T fields"],
                "disclaimer": (
                    "TaxMax AI provides AI-assisted preparation support and does not provide legal, "
                    "tax, or financial advice. Review all information with a qualified professional "
                    "before filing."
                ),
            }
        }
    )


class TaxOptimizationResponse(BaseModel):
    """Structured response for legal tax savings review."""

    status: ResponseStatus = Field(description="Overall optimization status.")
    opportunities: list[TaxSavingsOpportunity] = Field(default_factory=list)
    warnings: list[AgentWarning] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)
    review_package_summary: str = Field(
        default=(
            "TaxMax AI prepared a legal tax-savings review checklist. Confirm all facts "
            "and review opportunities with a qualified tax professional before filing."
        ),
    )
    disclaimer: str = Field(
        default=(
            "TaxMax AI identifies potential legal tax-saving opportunities for review. "
            "It does not provide legal, tax, or financial advice and does not guarantee "
            "a refund, lower tax, or eligibility for any deduction or credit."
        )
    )


class ChatRequest(BaseModel):
    """User chat message with optional tax scenario context."""

    message: str = Field(
        min_length=1,
        max_length=4000,
        description=(
            "User message to route through the TaxMax Guide workflow. Capped at "
            "4000 characters so oversized prompts are rejected with a 422 instead "
            "of consuming agent or model resources."
        ),
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional client session identifier for chat continuity.",
    )
    scenario: Optional[TaxScenarioRequest] = Field(
        default=None,
        description="Optional current tax scenario context for the assistant.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What information do you still need from me?",
                "session_id": "session_abc123",
                "scenario": None,
            }
        }
    )


class ChatResponse(BaseModel):
    """TaxMax Guide response for chat interactions."""

    status: ResponseStatus = Field(
        description="Overall response status for the chat interaction.",
    )
    answer: str = Field(
        description="Assistant response written in plain language without final eligibility claims.",
    )
    next_questions: list[str] = Field(
        default_factory=list,
        description="Follow-up questions the user can answer next.",
    )
    warnings: list[AgentWarning] = Field(
        default_factory=list,
        description="Any relevant warnings or uncertainty signals raised during chat.",
    )
    related_opportunities: list[TaxSavingsOpportunity] = Field(
        default_factory=list,
        description="Optional opportunities related to the user's message.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Information the assistant still needs from the user.",
    )
    disclaimer: str = Field(
        default=(
            "TaxMax AI provides AI-assisted preparation support and does not provide legal, "
            "tax, or financial advice. Review all information with a qualified professional "
            "before filing."
        ),
        description="Required user-facing disclaimer for chat responses.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "needs_more_information",
                "answer": "I can help organize the review, but I need a few more details before discussing possible options.",
                "next_questions": [
                    "Which tax year should I review?",
                    "Did you receive a Form 1098-T?",
                ],
                "warnings": [],
                "missing_information": ["Tax year", "Education document status"],
                "disclaimer": (
                    "TaxMax AI provides AI-assisted preparation support and does not provide legal, "
                    "tax, or financial advice. Review all information with a qualified professional "
                    "before filing."
                ),
            }
        }
    )


class DocumentExtractionResponse(BaseModel):
    """Safe response for document extraction requests."""

    status: ResponseStatus = Field(
        description="Current status of the document extraction request.",
    )
    message: str = Field(
        description="User-facing message describing extraction availability.",
    )
    document: Optional[DocumentInput] = Field(
        default=None,
        description="Document metadata received by the backend, if supplied.",
    )
    warnings: list[AgentWarning] = Field(
        default_factory=list,
        description="Warnings explaining why extraction is not yet available.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Information needed before a future extraction workflow can run.",
    )
    disclaimer: str = Field(
        default=(
            "TaxMax AI document extraction is not available yet. Do not rely on this "
            "stub for filing-ready tax document data."
        ),
        description="Required user-facing disclaimer for the extraction stub.",
    )
