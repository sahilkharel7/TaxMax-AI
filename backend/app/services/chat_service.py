"""Conversational chat service for TaxMax Guide.

This service is the primary entry point for the ``/api/chat`` endpoint. It

1. Tracks short-lived conversation history per ``session_id`` in memory.
2. Calls OpenAI's Chat Completions API when ``OPENAI_API_KEY`` is configured.
3. Falls back to a deterministic, safety-reviewed reply table when OpenAI is
   unavailable (no key, network error, empty completion, etc.).

The structured response surface (``status``, ``warnings``,
``missing_information``, ``next_questions``) is still derived from the supplied
scenario context, regardless of which backend produced the natural language
answer. That keeps the frontend's chat UI deterministic and gives the LLM the
same scaffolding to lean on.
"""

from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Optional

from app.schemas import (
    AgentWarning,
    ChatRequest,
    ChatResponse,
    ResponseStatus,
    TaxScenarioRequest,
)
from app.services.openai_client import (
    OpenAIChatError,
    OpenAINotConfiguredError,
    generate_chat_completion,
    is_openai_configured,
)


# --- Conversation memory ----------------------------------------------------

# Cap on how many prior turns (user+assistant messages) we replay to the LLM.
# 12 messages = roughly 6 full back-and-forth exchanges, which is enough to
# maintain context without exploding token usage.
_MAX_HISTORY_MESSAGES = 12

# Hard cap on the number of sessions we keep in memory so a long-running
# process can't grow without bound.
_MAX_TRACKED_SESSIONS = 256

_session_lock = threading.Lock()
_session_history: dict[str, Deque[dict[str, str]]] = {}


# --- System prompt ----------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are TaxMax Guide, the in-app assistant for TaxMax AI, a U.S. tax "
    "preparation prototype. Be warm, conversational, and concise (2-5 short "
    "sentences unless the user asks for detail). Use plain language and "
    "remember earlier turns in the same conversation.\n\n"
    "Scope and guardrails (these are firm):\n"
    "- You help users understand tax concepts (W-2, 1098-T, 1099 forms, "
    "  filing statuses, common credits and deductions), explain what each "
    "  step of the TaxMax flow does, and review information the user has "
    "  already provided.\n"
    "- You do NOT file returns. TaxMax AI cannot e-file or submit to the IRS "
    "  or any state. If a user asks you to file, say so clearly and suggest "
    "  an authorized preparer or e-file provider.\n"
    "- You do NOT promise exact refund amounts, exact tax owed, or final "
    "  eligibility for any credit or deduction. Numbers in the app are "
    "  estimates only.\n"
    "- You do NOT provide legal, tax, or financial advice. For situation-"
    "  specific questions, recommend confirming with a qualified tax "
    "  professional.\n"
    "- Never claim a user 'qualifies', 'is entitled to', or 'will receive' "
    "  anything. Prefer phrasing like 'may be eligible', 'commonly applies "
    "  when...', or 'a professional can confirm.'\n"
    "- If the user shares sensitive identifiers (SSN, full account numbers), "
    "  do not repeat them back. Acknowledge them generically.\n\n"
    "Style:\n"
    "- Friendly, calm, and direct. No emojis. No markdown headings.\n"
    "- When the user is mid-flow, gently point to the relevant TaxMax step "
    "  (Upload, Manual entry, Parsed review, Tax profile, Summary, Final "
    "  review) when helpful.\n"
    "- If the user's question is ambiguous, ask one clarifying question "
    "  rather than guessing."
)


# --- Public API -------------------------------------------------------------


def generate_chat_reply(request: ChatRequest) -> ChatResponse:
    """Generate a chat response, using OpenAI when configured.

    The structured signals (``status``, ``warnings``, ``missing_information``,
    ``next_questions``) come from the supplied scenario context. The free-form
    ``answer`` is produced by OpenAI when available, and otherwise by the
    deterministic fallback table.
    """

    status, warnings, missing = _scenario_signals(request.scenario)
    next_questions = _next_questions(request.scenario)

    answer, used_fallback = _generate_answer(request)
    if used_fallback and status == "draft" and not warnings and not missing:
        # No scenario context and no LLM -- keep status at "draft" which is
        # already the safe default for the deterministic placeholder.
        pass

    return ChatResponse(
        status=status,
        answer=answer,
        next_questions=next_questions,
        warnings=warnings,
        missing_information=missing,
    )


# --- Answer generation ------------------------------------------------------


def _generate_answer(request: ChatRequest) -> tuple[str, bool]:
    """Return ``(answer, used_fallback)`` for the given chat request."""

    if not is_openai_configured():
        return _fallback_reply(request.message), True

    session_id = (request.session_id or "").strip() or None
    history = _get_history_snapshot(session_id)

    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    scenario_context = _scenario_system_message(request.scenario)
    if scenario_context is not None:
        messages.append(scenario_context)
    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    try:
        answer = generate_chat_completion(messages)
    except (OpenAINotConfiguredError, OpenAIChatError):
        return _fallback_reply(request.message), True

    if session_id is not None:
        _record_turn(session_id, user_message=request.message, assistant_message=answer)

    return answer, False


def _scenario_system_message(
    scenario: Optional[TaxScenarioRequest],
) -> Optional[dict[str, str]]:
    """Render the current tax scenario as a compact system message."""

    if scenario is None:
        return None

    try:
        payload: dict[str, Any] = scenario.model_dump(
            mode="json", exclude_none=True, by_alias=False
        )
    except Exception:  # noqa: BLE001 -- never let serialization kill chat
        return None

    if not payload:
        return None

    return {
        "role": "system",
        "content": (
            "Current TaxMax scenario context (JSON, fields the user has "
            "entered so far). Treat unknown fields as 'not provided yet' "
            "rather than assuming a value:\n"
            + json.dumps(payload, default=str)
        ),
    }


# --- Conversation memory ----------------------------------------------------


def _get_history_snapshot(session_id: Optional[str]) -> list[dict[str, str]]:
    if session_id is None:
        return []

    with _session_lock:
        history = _session_history.get(session_id)
        if history is None:
            return []
        return list(history)


def _record_turn(
    session_id: str,
    *,
    user_message: str,
    assistant_message: str,
) -> None:
    with _session_lock:
        history = _session_history.get(session_id)
        if history is None:
            _evict_if_needed_locked()
            history = deque(maxlen=_MAX_HISTORY_MESSAGES)
            _session_history[session_id] = history

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})


def _evict_if_needed_locked() -> None:
    """Drop the oldest session if we're at capacity. Caller holds the lock."""

    if len(_session_history) < _MAX_TRACKED_SESSIONS:
        return
    oldest_key = next(iter(_session_history))
    _session_history.pop(oldest_key, None)


def reset_session(session_id: str) -> None:
    """Public helper -- mainly for tests -- to clear a single session."""

    with _session_lock:
        _session_history.pop(session_id, None)


def reset_all_sessions() -> None:
    """Public helper -- mainly for tests -- to clear all sessions."""

    with _session_lock:
        _session_history.clear()


# --- Deterministic fallback -------------------------------------------------
#
# These rules existed before the OpenAI integration and remain the canonical
# safe placeholder when no LLM is available. They are also exercised directly
# by the QA test suite (`tests/test_chat_endpoint.py`).


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
        re.compile(
            r"filing status|single|married|head of household|qss|hoh|mfj|mfs",
            re.IGNORECASE,
        ),
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


def _fallback_reply(message: str) -> str:
    for rule in _REPLY_RULES:
        if rule.pattern.search(message):
            return rule.answer
    return _DEFAULT_REPLY


# --- Scenario-derived structured signals ------------------------------------


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
