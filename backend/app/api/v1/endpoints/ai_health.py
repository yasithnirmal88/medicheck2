"""AI provider health API.

RBAC-gated (RESEARCH_REVIEWER+, same as the AI governance dashboard): reports
which AI/STT implementation is active for every consumer, whether credentials
are present, and — on demand (``?probe=true``) — whether the configured
vendor endpoint is reachable and authenticated.

Safety properties:
- NEVER exposes secret values (key presence only), patient data, prompts, or
  audio/transcripts.
- The default ``probe=false`` performs zero network I/O — safe to poll.
- ``probe=true`` issues a single lightweight ``GET {base_url}/models`` with
  the configured key (validates reachability + auth without spending
  inference tokens and without sending any PHI).
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.identity import User, get_ai_governance_user
from app.application.ai.provider_selection import (
    DEFAULT_OPENAI_BASE_URL,
    normalize_provider_name,
    resolve_llm_config,
    resolve_stt_config,
)
from app.core.config import settings
from app.core.exceptions import AIConfigurationError

router = APIRouter(prefix="/ai", tags=["ai-health"])

#: Probe timeout (seconds) — deliberately short; a health probe must not hang.
_PROBE_TIMEOUT_SECONDS = 5.0


class ProviderHealth(BaseModel):
    configured: str
    implementation: str
    credentials_present: bool = False
    model: str = ""
    base_url_host: str = ""
    error: str | None = None
    probe: str = "not_run"


class AIHealthResponse(BaseModel):
    explanation: ProviderHealth
    intake: ProviderHealth
    longitudinal: ProviderHealth
    stt: ProviderHealth
    queue: ProviderHealth


def _host(base_url: str) -> str:
    try:
        return urlparse(base_url).hostname or ""
    except Exception:
        return ""


def _probe_base(base_url: str, api_key: str) -> str:
    """Lightweight reachability + auth check. No PHI, no inference tokens."""
    url = base_url.rstrip("/") + "/models"
    try:
        resp = httpx.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(_PROBE_TIMEOUT_SECONDS),
        )
    except Exception:
        return "unreachable"
    if resp.status_code in (401, 403):
        return "auth_failed"
    if 200 <= resp.status_code < 300:
        return "healthy"
    return "unreachable"


def _llm_health(consumer: str, probe: bool) -> ProviderHealth:
    """Health for one AI_PROVIDER consumer (explanation/intake/longitudinal)."""
    from app.application.ai.intake_provider import get_intake_provider
    from app.application.ai.longitudinal_provider import get_longitudinal_provider
    from app.application.ai.provider import get_explanation_provider

    configured = normalize_provider_name(settings.ai_provider)
    factories = {
        "explanation": get_explanation_provider,
        "intake": get_intake_provider,
        "longitudinal": get_longitudinal_provider,
    }
    try:
        implementation = type(factories[consumer]()).__name__
    except AIConfigurationError as exc:
        return ProviderHealth(
            configured=configured,
            implementation="misconfigured",
            credentials_present=bool((settings.ai_api_key or "").strip()),
            model=(settings.ai_model or "").strip(),
            base_url_host=_host(
                (settings.ai_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL
            ),
            error=exc.detail,
            probe="misconfigured",
        )
    status = ProviderHealth(
        configured=configured,
        implementation=implementation,
        credentials_present=bool((settings.ai_api_key or "").strip()),
        model=(settings.ai_model or "").strip(),
        base_url_host=_host(
            (settings.ai_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL
        ),
    )
    if probe and implementation == "OpenAICompatibleChatProvider":
        try:
            cfg = resolve_llm_config(configured)
        except AIConfigurationError as exc:
            status.error = exc.detail
            status.probe = "misconfigured"
            return status
        status.probe = _probe_base(cfg.base_url, cfg.api_key)
    return status


def _stt_health(probe: bool) -> ProviderHealth:
    from app.application.ai.stt_provider import get_stt_provider

    configured = normalize_provider_name(getattr(settings, "stt_provider", None))
    try:
        implementation = type(get_stt_provider()).__name__
    except AIConfigurationError as exc:
        return ProviderHealth(
            configured=configured,
            implementation="misconfigured",
            credentials_present=bool((settings.stt_api_key or "").strip()),
            model=(settings.stt_model or "").strip(),
            base_url_host=_host(
                (settings.stt_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL
            ),
            error=exc.detail,
            probe="misconfigured",
        )
    status = ProviderHealth(
        configured=configured,
        implementation=implementation,
        credentials_present=bool((settings.stt_api_key or "").strip()),
        model=(settings.stt_model or "").strip(),
        base_url_host=_host(
            (settings.stt_base_url or "").strip() or DEFAULT_OPENAI_BASE_URL
        ),
    )
    if probe and implementation == "OpenAICompatibleSTTProvider":
        try:
            cfg = resolve_stt_config(configured)
        except AIConfigurationError as exc:
            status.error = exc.detail
            status.probe = "misconfigured"
            return status
        status.probe = _probe_base(cfg.base_url, cfg.api_key)
    return status


def _queue_health() -> ProviderHealth:
    from app.application.ai.queue_ranking_provider import get_queue_ranking_provider

    configured = normalize_provider_name(
        getattr(settings, "chw_queue_provider", None)
    )
    try:
        implementation = type(get_queue_ranking_provider()).__name__
    except AIConfigurationError as exc:
        return ProviderHealth(
            configured=configured,
            implementation="misconfigured",
            error=exc.detail,
            probe="misconfigured",
        )
    return ProviderHealth(configured=configured, implementation=implementation)


@router.get("/health", response_model=AIHealthResponse)
async def get_ai_health(
    current_user: User = Depends(get_ai_governance_user),
    probe: bool = Query(
        default=False,
        description=(
            "When true, perform a live reachability check against the "
            "configured vendor (GET /models, no PHI, no inference tokens)."
        ),
    ),
) -> AIHealthResponse:
    """AI/STT provider health for operators.

    Reports the resolved implementation per consumer, credential presence
    (never values), and optional live probe results. De-identified and
    PHI-free by construction.
    """
    return AIHealthResponse(
        explanation=_llm_health("explanation", probe),
        intake=_llm_health("intake", probe),
        longitudinal=_llm_health("longitudinal", probe),
        stt=_stt_health(probe),
        queue=_queue_health(),
    )
