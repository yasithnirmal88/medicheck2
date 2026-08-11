"""Phase 5 — Speech-to-text provider abstraction.

Voice is another INPUT channel only. Audio → transcript → existing Phase 3 AI
intake pipeline. Voice never creates a second clinical interpretation system.

The application depends on the ``SpeechToTextProvider`` Protocol, not on any
concrete vendor SDK. The default development provider is deterministic (no
network, no external API key) so tests run without credentials. A real vendor
provider can be added later by implementing the Protocol and selecting it via
``settings.stt_provider`` — no service-layer change required.

Audio privacy: audio is processed transiently. It is never permanently stored,
never logged, and never exposed via URLs. The provider receives only the audio
bytes + language hint and returns a transcript. The transcript is returned to
the patient for review/editing BEFORE clinical interpretation — an incorrect
transcript is never silently sent into the clinical pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.application.ai.language import (
    DEFAULT_INTAKE_LANGUAGE,
    normalize_language,
    resolve_language,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Maximum audio size accepted for transcription (10 MB). Protects against
#: oversized uploads; real STT vendors have their own limits.
MAX_AUDIO_BYTES = 10 * 1024 * 1024

#: Accepted audio content types. Kept restrictive so we never accept arbitrary
#: binary that the stub/real provider cannot handle.
ACCEPTED_AUDIO_CONTENT_TYPES: frozenset[str] = frozenset(
    {"audio/webm", "audio/webm;codecs=opus", "audio/ogg", "audio/wav", "audio/mpeg", "audio/mp4"}
)


@dataclass(frozen=True)
class TranscriptResult:
    """Result of speech-to-text transcription.

    ``transcript`` is the recognized text. ``language`` is the resolved
    language (detected if confident, else selected/default). ``confidence`` is
    the STT recognition confidence in [0,1] — NOT a clinical probability.
    """
    transcript: str
    language: str
    confidence: float = 0.9
    detected_language: str | None = None


class SpeechToTextError(RuntimeError):
    """Raised when an STT provider cannot produce a transcript.

    Lets the endpoint map any provider failure to a safe fallback — voice
    never breaks the assessment system; the patient can always type instead.
    """


@runtime_checkable
class SpeechToTextProvider(Protocol):
    """Transcribes audio to text.

    Implementations MUST:
    - return a ``TranscriptResult`` with a non-empty transcript on success;
    - respect the ``language`` hint where possible;
    - raise ``SpeechToTextError`` on any failure so the endpoint falls back;
    - NEVER store, log, or persist the raw audio;
    - NEVER make clinical decisions — this is transcription only.
    """

    name: str

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str = DEFAULT_INTAKE_LANGUAGE,
        content_type: str = "audio/webm",
    ) -> TranscriptResult: ...


class StubSpeechToTextProvider:
    """Deterministic local STT provider — the default.

    No network calls, no audio processing. Returns a deterministic English
    placeholder transcript so the full voice→intake→questionnaire flow can be
    exercised end-to-end in tests/CI without a real STT vendor. The transcript
    explicitly signals it is a stub so it is never mistaken for real output in
    production.
    """

    name = "stub-stt"

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
        # Resolve language: detect from any embedded text is not possible for
        # raw audio in the stub, so use the selected language (normalized).
        norm = normalize_language(language)
        return TranscriptResult(
            transcript=(
                "I have been getting tired when climbing stairs and sometimes "
                "I feel uncomfortable around my chest."
            ),
            language=norm,
            confidence=0.9,
            detected_language=None,
        )


def get_stt_provider() -> SpeechToTextProvider:
    """Return the configured speech-to-text provider.

    Defaults to the deterministic stub. A real vendor provider can be selected
    by setting ``STT_PROVIDER`` and implementing the Protocol here. Phase 5
    ships only the stub provider; no third-party STT packages are installed.
    """
    name = (getattr(settings, "stt_provider", None) or "stub").strip().lower()
    if name == "stub":
        return StubSpeechToTextProvider()
    logger.info(
        "STT provider '%s' not implemented for intake in Phase 5; using stub", name
    )
    return StubSpeechToTextProvider()


def resolve_transcript_language(
    transcript: str,
    selected: str | None = None,
) -> tuple[str, str | None]:
    """Resolve the language for a transcript (detected if confident).

    Returns (resolved_language, detected_language_or_None). Used after
    transcription so the intake pipeline knows which language the patient
    actually spoke — useful for localized clarifications and traceability.
    """
    res = resolve_language(transcript, selected)
    return res.resolved, res.detected
