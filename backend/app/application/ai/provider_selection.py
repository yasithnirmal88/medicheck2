"""Shared AI/STT provider selection.

Centralizes provider-name normalization and the fail-fast contract so every
factory (`get_explanation_provider`, `get_intake_provider`,
`get_longitudinal_provider`, `get_stt_provider`, `get_queue_ranking_provider`)
behaves identically:

- Known stub names  → caller builds its deterministic stub (safe default).
- Known real names   → validated config is returned; the caller builds the
  HTTP provider. Missing credentials/endpoints raise ``AIConfigurationError``.
- Anything else     → ``AIConfigurationError``. Unknown names NEVER silently
  fall back to a stub: an operator who configures ``AI_PROVIDER=openai``
  without a key must get a loud error, not stub output masquerading as the
  real vendor.

No secrets are ever included in error messages or logs — presence only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import AIConfigurationError

#: Default OpenAI-compatible base URL used when no explicit base URL is set.
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

#: Default transcription model for the OpenAI-compatible STT provider.
DEFAULT_STT_MODEL = "whisper-1"

#: LLM provider names served by deterministic local stubs.
LLM_STUB_NAMES = frozenset({"stub", "personalized-stub"})

#: LLM provider names served by the OpenAI-compatible HTTP provider.
LLM_HTTP_NAMES = frozenset({"openai", "openai-compatible"})

#: STT provider names served by deterministic local stubs.
STT_STUB_NAMES = frozenset({"stub", "stub-stt"})

#: STT provider names served by the OpenAI-compatible HTTP STT provider.
STT_HTTP_NAMES = frozenset({"openai", "whisper", "openai-compatible"})


def normalize_provider_name(raw: str | None) -> str:
    """Normalize a configured provider name (lowercase, stripped)."""
    return (raw or "stub").strip().lower()


@dataclass(frozen=True)
class LLMConfig:
    """Validated config for an OpenAI-compatible chat provider."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    max_retries: int


@dataclass(frozen=True)
class STTConfig:
    """Validated config for an OpenAI-compatible transcription provider."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    max_retries: int


def resolve_llm_config(raw_name: str | None) -> LLMConfig:
    """Validate settings for a real LLM provider name.

    Raises ``AIConfigurationError`` for unknown names and for missing
    credentials/model. Never includes secret values in the message.
    """
    name = normalize_provider_name(raw_name)
    if name in LLM_STUB_NAMES:
        raise AIConfigurationError(
            detail=f"AI provider '{name}' is a stub; no real-provider config to resolve"
        )
    if name not in LLM_HTTP_NAMES:
        raise AIConfigurationError(
            detail=(
                f"Unknown AI_PROVIDER '{name}'. Expected one of: "
                f"{sorted(LLM_STUB_NAMES | LLM_HTTP_NAMES)}"
            )
        )
    api_key = (settings.ai_api_key or "").strip()
    model = (settings.ai_model or "").strip()
    if not api_key:
        raise AIConfigurationError(
            detail=(
                f"AI_PROVIDER '{name}' requires AI_API_KEY to be set "
                "(refusing to run without credentials)"
            )
        )
    if not model:
        raise AIConfigurationError(
            detail=(
                f"AI_PROVIDER '{name}' requires AI_MODEL to be set "
                "(refusing to run without an explicit model)"
            )
        )
    return LLMConfig(
        base_url=(settings.ai_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL,
        api_key=api_key,
        model=model,
        timeout_seconds=settings.ai_request_timeout_seconds,
        max_retries=max(0, settings.ai_max_retries),
    )


def resolve_stt_config(raw_name: str | None) -> STTConfig:
    """Validate settings for a real STT provider name.

    Raises ``AIConfigurationError`` for unknown names and for missing
    credentials. The model defaults to ``whisper-1`` when unset.
    """
    name = normalize_provider_name(raw_name)
    if name in STT_STUB_NAMES:
        raise AIConfigurationError(
            detail=f"STT provider '{name}' is a stub; no real-provider config to resolve"
        )
    if name not in STT_HTTP_NAMES:
        raise AIConfigurationError(
            detail=(
                f"Unknown STT_PROVIDER '{name}'. Expected one of: "
                f"{sorted(STT_STUB_NAMES | STT_HTTP_NAMES)}"
            )
        )
    api_key = (settings.stt_api_key or "").strip()
    if not api_key:
        raise AIConfigurationError(
            detail=(
                f"STT_PROVIDER '{name}' requires STT_API_KEY to be set "
                "(refusing to run without credentials)"
            )
        )
    return STTConfig(
        base_url=(settings.stt_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL,
        api_key=api_key,
        model=(settings.stt_model or "").strip() or DEFAULT_STT_MODEL,
        timeout_seconds=settings.stt_request_timeout_seconds,
        max_retries=max(0, settings.ai_max_retries),
    )
