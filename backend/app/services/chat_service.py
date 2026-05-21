"""Chat reply service.

This is a deterministic placeholder so the frontend can integrate with the
backend before the Gemini-powered agent workflow is wired in. Swap this
implementation with the real agent orchestrator when it is ready; the public
`generate_chat_reply` signature is intentionally stable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.schemas import (
    AgentWarning,
    ChatRequest,
    ChatResponse,
    ResponseStatus,
    TaxScenarioRequest,
)


@dataclass(frozen=True)
class _ReplyRule:
    pattern: re.Pattern[str]
    answer: str


_REPLY_RULES: tuple[_ReplyRule, ...] = (
    _ReplyRule(
        re.compile(
            r"\b(file|e-?file|submit|send)\b.*\b(irs|return|taxes?)\b"
            r"|\b(can|do|will) you file\b"
            r"|\bfile (my|the) (taxes?|return)\b",
            re.IGNORECASE,
        ),
        (
            "TaxMax AI cannot file your return with the IRS or any state tax "
            "authority. E-filing is not available in this prototype. I can help "
            "you organize and review your information, but you will need to "
            "file through an authorized preparer or e-file provider."
        ),
    ),
    _ReplyRule(
        re.compile(
            r"\b(guarantee|guaranteed|definitely|for sure|exactly)\b.*"
            r"\b(refund|owe|qualify|eligible|amount|get)\b"
            r"|\bhow much (refund|will i get|do i (get|owe))\b"
            r"|\bdo i (qualify|get|definitely)\b",
            re.IGNORECASE,
        ),
        (
            "I can\u2019t confirm an exact refund amount or final eligibility "
            "for any credit. TaxMax AI is a review-stage tool only \u2014 "
            "final amounts and final eligibility require a complete return "
            "and a qualified tax professional."
        ),
    ),
    _ReplyRule(
        re.compile(r"w-?2", re.IGNORECASE),
        (
            "A W-2 is the wage statement your employer sends each January. "
            "It reports your wages and the federal, state, Social Security, "
            "and Medicare taxes that were withheld. Box 1 shows your total "
            "taxable wages, and Box 2 shows the federal income tax that was "
            "withheld."
        ),
    ),
    _ReplyRule(
        re.compile(r"box ?1", re.IGNORECASE),
        (
            "Box 1 of your W-2 is in the upper right area of the form and is "
            "labeled \u201cWages, tips, other compensation.\u201d That number "
            "is your federal taxable wages for the year."
        ),
    ),
    _ReplyRule(
        re.compile(r"1098-?t", re.IGNORECASE),
        (
            "A 1098-T reports tuition payments and scholarships from an "
            "eligible educational institution. You generally need it if you "
            "(or a dependent) were enrolled in higher education and want to "
            "explore education credits like the American Opportunity Credit "
            "or Lifetime Learning Credit."
        ),
    ),
    _ReplyRule(
        re.compile(r"dependent", re.IGNORECASE),
        (
            "Whether someone can claim you as a dependent depends on factors "
            "like age, student status, residency, and financial support. "
            "Based on your answers, I can highlight the requirements to "
            "review with a qualified tax professional."
        ),
    ),
    _ReplyRule(
        re.compile(r"review|extracted|parse", re.IGNORECASE),
        (
            "Document parsing can sometimes misread numbers, especially on "
            "scanned PDFs. Reviewing each extracted value before moving "
            "forward is the easiest way to catch typos and make sure your "
            "return reflects your actual documents."
        ),
    ),
    _ReplyRule(
        re.compile(r"upload|document", re.IGNORECASE),
        (
            "For most simple returns, you\u2019ll want your W-2 from each "
            "employer, any 1099 forms (1099-INT, 1099-NEC, 1099-DIV), and a "
            "1098-T if you paid tuition. You can also enter information "
            "manually if you don\u2019t have the PDFs."
        ),
    ),
    _ReplyRule(
        re.compile(r"refund|owe|estimate", re.IGNORECASE),
        (
            "The summary screen shows a rough estimate based on the "
            "information you\u2019ve entered. It\u2019s not final \u2014 "
            "your actual refund or balance due depends on the full return "
            "and a complete review."
        ),
    ),
    _ReplyRule(
        re.compile(r"filing status|single|married|head of household|qss|hoh|mfj|mfs", re.IGNORECASE),
        (
            "Filing status is one of single, married filing jointly, married "
            "filing separately, head of household, or qualifying surviving "
            "spouse. The right choice depends on marital status, dependents, "
            "and household support \u2014 confirm with a qualified preparer "
            "before filing."
        ),
    ),
)

_DEFAULT_REPLY = (
    "I can explain tax terms and walk you through this app step by step. "
    "Try asking about W-2s, 1098-Ts, filing status, or how the review step "
    "works. For anything specific to your situation, please confirm with a "
    "qualified tax professional."
)


def generate_chat_reply(request: ChatRequest) -> ChatResponse:
    """Return a deterministic, schema-valid chat response.

    The reply text is a placeholder until the Gemini-backed agent workflow
    replaces this implementation. Status, warnings, and missing information
    fields are still derived from the supplied scenario context so the
    frontend can render its full chat UI today.
    """

    answer = _match_reply(request.message)
    status, warnings, missing = _scenario_signals(request.scenario)
    next_questions = _next_questions(request.scenario)

    return ChatResponse(
        status=status,
        answer=answer,
        next_questions=next_questions,
        warnings=warnings,
        missing_information=missing,
    )


def _match_reply(message: str) -> str:
    for rule in _REPLY_RULES:
        if rule.pattern.search(message):
            return rule.answer
    return _DEFAULT_REPLY


def _scenario_signals(
    scenario: Optional[TaxScenarioRequest],
) -> tuple[ResponseStatus, list[AgentWarning], list[str]]:
    if scenario is None:
        return "draft", [], []

    missing: list[str] = []
    warnings: list[AgentWarning] = []
    profile = scenario.profile

    if profile.tax_year is None:
        missing.append("Tax year")
    if profile.filing_status is None:
        missing.append("Filing status")
    if profile.was_student is True and profile.received_1098_t is None:
        missing.append("Form 1098-T status")
        warnings.append(
            AgentWarning(
                severity="low",
                code="MISSING_1098_T_STATUS",
                message="Student status was indicated but 1098-T receipt is unknown.",
                recommended_follow_up="Ask whether the user received Form 1098-T.",
            )
        )

    status: ResponseStatus = "needs_more_information" if missing else "draft"
    return status, warnings, missing


def _next_questions(scenario: Optional[TaxScenarioRequest]) -> list[str]:
    if scenario is None:
        return [
            "Which tax year would you like to review?",
            "Do you have your W-2 or other tax documents ready?",
        ]

    questions: list[str] = []
    profile = scenario.profile
    if profile.tax_year is None:
        questions.append("Which tax year should I review?")
    if profile.filing_status is None:
        questions.append("What filing status are you considering?")
    if profile.was_student is True and profile.received_1098_t is None:
        questions.append("Did you receive a Form 1098-T from your school?")
    if profile.received_1099 is True and (
        scenario.income is None or scenario.income.self_employment_income is None
    ):
        questions.append(
            "Do you know whether the 1099 income was self-employment or interest income?"
        )
    return questions
