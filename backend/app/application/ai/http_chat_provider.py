"""OpenAI-compatible HTTP chat provider.

One concrete class serves the three LLM Protocols — ``AIExplanationProvider``
(``explain``), ``AIClinicalIntakeProvider`` (``extract_candidates``) and
``LongitudinalExplanationProvider`` (``explain_trajectory``) — because all
three are the same shape: serialize a deterministic, PHI-scrubbed context into
a user message, POST it to a chat-completions endpoint, return the raw JSON
string. Parsing + allow-list validation stay in the service layer, which is
what keeps the LLM an explanation/extraction layer only.

Endpoint contract (OpenAI-compatible):
- ``POST {base_url}/chat/completions`` with Bearer auth,
- ``{"model", "messages", "temperature": 0, "response_format": {"type":
  "json_object"}}``,
- response ``choices[0].message.content`` is the raw JSON string.

Safety properties:
- ``temperature=0`` for deterministic, reproducible output.
- The versioned system prompts (Phase 1 v2.0 / intake 1.0 / longitudinal 1.0)
  are reused verbatim — the same non-diagnostic binding as the stubs.
- Timeouts come from ``settings.ai_request_timeout_seconds``; retries
  (``settings.ai_max_retries``) apply to transient failures only (HTTP
  429/5xx, network errors). Auth/client errors (other 4xx) fail immediately.
- Every failure raises the calling Protocol's own error type
  (``AIProviderError`` / ``AIIntakeProviderError`` / longitudinal
  ``AIProviderError``) so existing service fallbacks + audit trails engage
  unchanged. API keys and response bodies are never logged.
- No vendor SDK dependency — plain ``httpx`` (already a project dependency).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.application.ai.intake_provider import AIIntakeProviderError
from app.application.ai.intake_prompts import INTAKE_SYSTEM_PROMPT
from app.application.ai.longitudinal_prompts import LONGITUDINAL_SYSTEM_PROMPT
from app.application.ai.longitudinal_provider import (
    AIProviderError as LongitudinalProviderError,
)
from app.application.ai.prompts import SYSTEM_PROMPT
from app.application.ai.provider import AIProviderError
from app.application.ai.provider_selection import LLMConfig
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Path suffix for chat completions on OpenAI-compatible endpoints.
CHAT_COMPLETIONS_PATH = "/chat/completions"


def _safe_message(status_code: int | None, kind: str) -> str:
    """Short, secret-free failure message for logs/audit."""
    if status_code is None:
        return f"openai-compatible {kind} request failed (network/timeout)"
    return f"openai-compatible {kind} request failed (http {status_code})"


class OpenAICompatibleChatProvider:
    """HTTP chat provider for explanation, intake extraction, and trajectory
    explanation. Construct via ``from_config`` or with explicit arguments
    (tests inject an ``httpx.AsyncClient`` backed by ``MockTransport``).
    """

    name = "openai-compatible"

    #: Metered vendor calls go through the AI spend guardrails. Stubs leave
    #: this False (via getattr default) and bypass budgets entirely.
    metered = True

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 1,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self._http_client = http_client

    @classmethod
    def from_config(cls, config: LLMConfig) -> OpenAICompatibleChatProvider:
        return cls(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    # ── Protocol methods ──────────────────────────────────────────────

    async def explain(self, context: Any) -> str:
        """AIExplanationProvider: explain a deterministic report (RAG-aware)."""
        user_message = (
            "Assessment context (JSON). Explain ONLY what is in this context:\n"
            + _dump_context(context)
        )
        try:
            return await self._chat(
                SYSTEM_PROMPT, user_message, kind="explanation"
            )
        except AIProviderError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("openai-compatible explanation failed: %r", type(exc).__name__)
            raise AIProviderError("openai-compatible explanation failure") from exc

    async def extract_candidates(self, context: Any) -> str:
        """AIClinicalIntakeProvider: extract observations + candidates."""
        catalog = getattr(context, "catalog", None)
        entries = getattr(catalog, "entries", []) or []
        user_message = (
            "Patient message:\n"
            f"{getattr(context, 'patient_message', '')}\n\n"
            f"Language: {getattr(context, 'language', 'en')} "
            f"(input_type={getattr(context, 'input_type', 'text')}).\n"
            "Indicator catalog (JSON — cite ONLY these indicator_id values):\n"
            + json.dumps(
                [e.model_dump(mode="json") for e in entries],
                sort_keys=True,
                default=str,
            )
        )
        try:
            return await self._chat(
                INTAKE_SYSTEM_PROMPT, user_message, kind="intake"
            )
        except AIProviderError as exc:
            # Map to the intake Protocol's own error type so the intake
            # service fallback engages.
            raise AIIntakeProviderError(str(exc)) from exc

    async def explain_trajectory(self, context: Any) -> str:
        """LongitudinalExplanationProvider: explain a deterministic trajectory."""
        user_message = (
            "Longitudinal trajectory context (JSON). "
            "Explain ONLY the changes described here:\n" + _dump_context(context)
        )
        try:
            return await self._chat(
                LONGITUDINAL_SYSTEM_PROMPT, user_message, kind="trajectory"
            )
        except AIProviderError as exc:
            raise LongitudinalProviderError(str(exc)) from exc

    # ── HTTP core ─────────────────────────────────────────────────────

    async def _chat(
        self, system_prompt: str, user_message: str, *, kind: str
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        url = self.base_url + CHAT_COMPLETIONS_PATH
        headers = {"Authorization": f"Bearer {self._api_key}"}
        timeout = httpx.Timeout(self.timeout_seconds)

        attempts = 1 + self.max_retries
        last_status: int | None = None
        for attempt in range(1, attempts + 1):
            client, owned = self._client()
            try:
                resp = await client.post(
                    url, json=payload, headers=headers, timeout=timeout
                )
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                logger.warning(
                    "openai-compatible %s attempt %d/%d transport failure: %r",
                    kind,
                    attempt,
                    attempts,
                    type(exc).__name__,
                )
                last_status = None
                if attempt < attempts:
                    await asyncio.sleep(0.25 * attempt)
                    continue
                raise AIProviderError(_safe_message(None, kind)) from exc
            finally:
                if owned:
                    await client.aclose()

            if resp.status_code == 429 or resp.status_code >= 500:
                last_status = resp.status_code
                logger.warning(
                    "openai-compatible %s attempt %d/%d retryable status %d",
                    kind,
                    attempt,
                    attempts,
                    resp.status_code,
                )
                if attempt < attempts:
                    await asyncio.sleep(0.25 * attempt)
                    continue
                raise AIProviderError(_safe_message(resp.status_code, kind))
            if resp.status_code >= 400:
                # Auth/client errors fail immediately — never retry, and never
                # leak the key or body.
                raise AIProviderError(_safe_message(resp.status_code, kind))
            return _extract_content(resp, kind)

        raise AIProviderError(_safe_message(last_status, kind))

    def _client(self) -> tuple[httpx.AsyncClient, bool]:
        """Return (client, owned). Injected clients are never closed here."""
        if self._http_client is not None:
            return self._http_client, False
        return httpx.AsyncClient(), True


def _dump_context(context: Any) -> str:
    """Deterministic JSON serialization of a provider context DTO."""
    if hasattr(context, "model_dump"):
        data = context.model_dump(mode="json")
    elif isinstance(context, dict):
        data = context
    else:
        data = {"context": str(context)}
    return json.dumps(data, sort_keys=True, default=str)


def _extract_content(resp: httpx.Response, kind: str) -> str:
    """Pull the assistant message text out of a chat-completions response."""
    try:
        data = resp.json()
    except Exception as exc:
        raise AIProviderError(
            f"openai-compatible {kind} returned a non-JSON response"
        ) from exc
    try:
        choices = data.get("choices") or []
        content = choices[0].get("message", {}).get("content")
    except (IndexError, AttributeError, TypeError) as exc:
        raise AIProviderError(
            f"openai-compatible {kind} response has no usable choice"
        ) from exc
    text = _content_to_text(content)
    if not text:
        raise AIProviderError(
            f"openai-compatible {kind} returned an empty completion"
        )
    return _strip_fences(text)


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            p.get("text", "")
            for p in content
            if isinstance(p, dict) and isinstance(p.get("text"), str)
        ]
        return "".join(parts).strip()
    return ""


def _strip_fences(text: str) -> str:
    """Remove ```json fences some models add despite JSON-only instructions.

    The service layer still parses + validates the result, so this is a
    robustness convenience, not a trust decision.
    """
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    lines = lines[1:]  # drop opening fence (``` or ```json)
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
