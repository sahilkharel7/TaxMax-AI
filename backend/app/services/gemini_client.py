from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import get_settings


DEFAULT_GEMINI_TIMEOUT_MS = 30_000


class GeminiNotConfiguredError(RuntimeError):
    """Raised when Gemini is requested without a server-side API key."""


class GeminiFallbackResponse(BaseModel):
    """Controlled fallback returned when Gemini cannot produce usable JSON."""

    status: str = Field(description="Fallback status.")
    response_schema_name: str = Field(description="Requested response schema name.")
    message: str = Field(description="Safe user-facing failure message.")
    retryable: bool = Field(description="Whether retrying later may succeed.")


def generate_structured_agent_response(
    system_prompt: str,
    user_payload: dict[str, Any],
    response_schema_name: str,
) -> dict[str, Any]:
    """Generate and parse a structured Gemini response.

    This function intentionally does not log prompts or tax payloads. Callers get
    parsed JSON on success, or a controlled fallback dictionary for recoverable
    Gemini/parsing failures.
    """

    settings = get_settings()
    api_key = _gemini_api_key(settings.gemini_api_key)
    if not api_key:
        raise GeminiNotConfiguredError(
            "Gemini is not configured. Set GEMINI_API_KEY in the backend environment."
        )

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=DEFAULT_GEMINI_TIMEOUT_MS),
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_safe_user_content(user_payload, response_schema_name),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )
    except (TimeoutError, httpx.TimeoutException):
        return _fallback(
            response_schema_name=response_schema_name,
            message="Gemini request timed out before a structured response was available.",
            retryable=True,
        )
    except Exception:
        return _fallback(
            response_schema_name=response_schema_name,
            message="Gemini could not generate a structured response safely.",
            retryable=True,
        )

    parsed = _parsed_response(response)
    if parsed is None:
        return _fallback(
            response_schema_name=response_schema_name,
            message="Gemini returned a response that could not be parsed as JSON.",
            retryable=False,
        )

    return parsed


def _gemini_api_key(settings_api_key: str) -> str:
    return os.getenv("GEMINI_API_KEY") or settings_api_key


def _safe_user_content(user_payload: dict[str, Any], response_schema_name: str) -> str:
    return json.dumps(
        {
            "response_schema_name": response_schema_name,
            "payload": user_payload,
            "instructions": [
                "Return only valid JSON.",
                "Do not calculate final taxes.",
                "Do not make final eligibility claims.",
            ],
        },
        default=str,
    )


def _parsed_response(response: Any) -> Optional[dict[str, Any]]:
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, dict):
        return parsed

    text = getattr(response, "text", None)
    if not text:
        return None

    try:
        loaded = json.loads(_strip_json_fence(text))
    except json.JSONDecodeError:
        return None

    if isinstance(loaded, dict):
        return loaded
    return None


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _fallback(
    *,
    response_schema_name: str,
    message: str,
    retryable: bool,
) -> dict[str, Any]:
    return GeminiFallbackResponse(
        status="fallback",
        response_schema_name=response_schema_name,
        message=message,
        retryable=retryable,
    ).model_dump()
