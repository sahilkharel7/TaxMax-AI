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


class HealthResponse(BaseModel):
    status: str = Field(description="Health status for the API service.")
    service: str = Field(description="Human-readable API service name.")


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
    documents: list[DocumentInput] = Field(
        default_factory=list,
        description="Uploaded or parsed tax documents available to the agent workflow.",
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


class ChatRequest(BaseModel):
    """User chat message with optional tax scenario context."""

    message: str = Field(
        min_length=1,
        description="User message to route through the TaxMax Guide workflow.",
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
