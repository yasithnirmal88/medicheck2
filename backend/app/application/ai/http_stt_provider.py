"""OpenAI-compatible HTTP speech-to-text provider.

Implements the ``SpeechToTextProvider`` Protocol over the OpenAI-compatible
transcription endpoint:

- ``POST {base_url}/audio/transcriptions`` (multipart: file + model +
  language + response_format=json),
- response ``{"text": "..."}`` becomes the transcript.

Voice remains an INPUT channel only: audio → transcript → patient
review/edit → existing Phase 3 intake pipeline. The transcript is returned to
the patient for review BEFORE clinical interpretation, exactly as with the
stub.

Safety properties:
- Audio is transient: validated (non-empty, ≤ ``MAX_AUDIO_BYTES``), sent once,
  never stored, never logged, never exposed via URLs. Error messages and logs
  carry sizes/statuses only — never audio bytes or transcripts.
- Timeouts from ``settings.stt_request_timeout_seconds``; retries
  (``settings.ai_max_retries``) on transient failures only (HTTP 429/5xx,
  network errors). Auth/client errors fail immediately.
- Every failure raises ``SpeechToTextError`` so the endpoint falls back to
  "type instead" — voice never breaks the assessment system.
- No vendor SDK dependency — plain ``httpx`` (already a project dependency).
"""

from __future__ import annotations

import asyncio
import re

import httpx

from app.application.ai.language import (
    DEFAULT_INTAKE_LANGUAGE,
    normalize_language,
)
from app.application.ai.provider_selection import STTConfig
from app.application.ai.stt_provider import (
    MAX_AUDIO_BYTES,
    SpeechToTextError,
    TranscriptResult,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Path suffix for transcriptions on OpenAI-compatible endpoints.
TRANSCRIPTIONS_PATH = "/audio/transcriptions"

#: Two-letter language hint passthrough (Whisper-compatible ISO-639-1 codes).
_LANGUAGE_HINT_RE = re.compile(r"^[a-z]{2}$")

#: File extension by accepted content type (for the multipart filename).
_EXTENSION_BY_CONTENT_TYPE = {
    "audio/webm": "webm",
    "audio/webm;codecs=opus": "webm",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp4": "mp4",
}


class OpenAICompatibleSTTProvider:
    """HTTP transcription provider. Construct via ``from_config`` or with
    explicit arguments (tests inject an ``httpx.AsyncClient`` backed by
    ``MockTransport``).
    """

    name = "openai-compatible"

    #: See OpenAICompatibleChatProvider.metered.
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
    def from_config(cls, config: STTConfig) -> OpenAICompatibleSTTProvider:
        return cls(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str = DEFAULT_INTAKE_LANGUAGE,
        content_type: str = "audio/webm",
    ) -> TranscriptResult:
        if not audio_bytes:
            raise SpeechToTextError("empty audio")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise SpeechToTextError("audio too large")

        norm = normalize_language(language)
        hint = norm if _LANGUAGE_HINT_RE.match(norm) else None

        url = self.base_url + TRANSCRIPTIONS_PATH
        headers = {"Authorization": f"Bearer {self._api_key}"}
        extension = _EXTENSION_BY_CONTENT_TYPE.get(
            (content_type or "").lower(), "webm"
        )
        data: dict[str, str] = {"model": self.model, "response_format": "json"}
        if hint:
            data["language"] = hint
        files = {"file": (f"audio.{extension}", audio_bytes, content_type)}
        timeout = httpx.Timeout(self.timeout_seconds)

        attempts = 1 + self.max_retries
        for attempt in range(1, attempts + 1):
            client, owned = self._client()
            try:
                resp = await client.post(
                    url, headers=headers, data=data, files=files, timeout=timeout
                )
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                logger.warning(
                    "openai-compatible stt attempt %d/%d transport failure: %r",
                    attempt,
                    attempts,
                    type(exc).__name__,
                )
                if attempt < attempts:
                    await asyncio.sleep(0.25 * attempt)
                    continue
                raise SpeechToTextError("transcription service unreachable") from exc
            finally:
                if owned:
                    await client.aclose()

            if resp.status_code == 429 or resp.status_code >= 500:
                logger.warning(
                    "openai-compatible stt attempt %d/%d retryable status %d",
                    attempt,
                    attempts,
                    resp.status_code,
                )
                if attempt < attempts:
                    await asyncio.sleep(0.25 * attempt)
                    continue
                raise SpeechToTextError(
                    f"transcription service error (http {resp.status_code})"
                )
            if resp.status_code >= 400:
                raise SpeechToTextError(
                    f"transcription request rejected (http {resp.status_code})"
                )
            return _to_result(resp, norm)

        raise SpeechToTextError("transcription service unreachable")

    def _client(self) -> tuple[httpx.AsyncClient, bool]:
        """Return (client, owned). Injected clients are never closed here."""
        if self._http_client is not None:
            return self._http_client, False
        return httpx.AsyncClient(), True


def _to_result(resp: httpx.Response, language: str) -> TranscriptResult:
    """Parse a transcription response. Never logs audio or transcripts."""
    try:
        data = resp.json()
    except Exception as exc:
        raise SpeechToTextError("transcription returned a non-JSON response") from exc
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise SpeechToTextError("transcription returned an empty transcript")
    return TranscriptResult(
        transcript=text.strip(),
        language=language,
        detected_language=None,
    )
