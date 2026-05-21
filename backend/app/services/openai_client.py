"""Thin OpenAI client wrapper used by the conversational chat service.

The goal of this module is to keep all `openai` SDK details in one place so the
chat service can stay focused on prompt assembly and conversation memory.

No prompts, message contents, or scenario payloads are logged here.
"""

from __future__ import annotations

import os
from typing import Iterable

from openai import APIError, APITimeoutError, OpenAI

from app.config import get_settings


DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_TOKENS = 600


class OpenAINotConfiguredError(RuntimeError):
    """Raised when OpenAI is requested without a server-side API key."""


class OpenAIChatError(RuntimeError):
    """Raised when OpenAI fails to produce a usable chat completion."""


def is_openai_configured() -> bool:
    """Return True when an OpenAI API key is present in the environment."""

    return bool(_resolve_api_key())


def generate_chat_completion(
    messages: Iterable[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Call OpenAI Chat Completions and return the assistant text.

    Args:
        messages: Ordered chat messages with ``role`` and ``content`` keys.
        temperature: Sampling temperature; kept low for tax guidance accuracy.
        max_tokens: Hard cap on the response size to bound cost and latency.

    Raises:
        OpenAINotConfiguredError: When no API key is configured.
        OpenAIChatError: When the API call fails or returns an empty reply.
    """

    api_key = _resolve_api_key()
    if not api_key:
        raise OpenAINotConfiguredError(
            "OpenAI is not configured. Set OPENAI_API_KEY in the backend environment.",
        )

    settings = get_settings()
    client = OpenAI(api_key=api_key, timeout=DEFAULT_TIMEOUT_SECONDS)

    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=list(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except APITimeoutError as exc:
        raise OpenAIChatError("OpenAI request timed out.") from exc
    except APIError as exc:
        raise OpenAIChatError(f"OpenAI API error: {exc.__class__.__name__}") from exc
    except Exception as exc:  # noqa: BLE001 -- shield callers from unexpected SDK errors
        raise OpenAIChatError("Unexpected OpenAI client error.") from exc

    choices = getattr(completion, "choices", None) or []
    if not choices:
        raise OpenAIChatError("OpenAI returned no choices.")

    message = getattr(choices[0], "message", None)
    text = getattr(message, "content", None) if message is not None else None
    if not text or not text.strip():
        raise OpenAIChatError("OpenAI returned an empty message.")

    return text.strip()


def _resolve_api_key() -> str:
    """Return the OpenAI API key from env first, then settings."""

    env_value = os.getenv("OPENAI_API_KEY")
    if env_value:
        return env_value.strip()

    settings_value = get_settings().openai_api_key
    return (settings_value or "").strip()
