"""Phase 3/5 — AI clinical-intake endpoints.

POST /api/v1/ai/intake/extract          — multilingual text/voice intake
POST /api/v1/ai/intake/transcribe       — speech-to-text (transient, no storage)
GET  /api/v1/ai/intake/languages        — supported intake languages

Authentication: existing ``get_current_user`` dependency (RBAC preserved; no
CMS permissions required for patient intake). Session ownership is verified:
if a ``session_id`` is supplied it must belong to the authenticated user. The
intake is scoped to the caller — no cross-patient intake.

The endpoint never modifies the deterministic pipeline. The intake response is
session-scoped; AI output is validated against the authoritative knowledge
graph before it can influence question selection. On any failure, a safe
fallback (``available=false``) is returned so the standard questionnaire keeps
working.

Phase 5: ``language`` carries the user-selected language; the system also
performs best-effort script detection. Localized input always resolves to the
SAME canonical indicator IDs — the language layer is an interface layer only.
Voice input is transcribed to text, reviewed/edited by the patient, THEN fed
into the same Phase 3 intake pipeline. Audio is never stored or logged.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.ai.language import (
    LANGUAGE_LABELS,
    SUPPORTED_INTAKE_LANGUAGES,
    is_supported_language,
    normalize_language,
)
from app.application.ai.stt_provider import (
    ACCEPTED_AUDIO_CONTENT_TYPES,
    MAX_AUDIO_BYTES,
    SpeechToTextError,
)
from app.application.dtos.intake_dtos import IntakeResponse
from app.application.services.ai_intake_service import AIIntakeService
from app.core.logging import get_logger
from app.infrastructure.database import get_db
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/ai/intake", tags=["ai-intake"])


class IntakeExtractRequest(BaseModel):
    """Request body for AI intake extraction.

    ``session_id`` is optional: it ties the intake to an existing assessment
    session (ownership verified). When omitted, a pseudonymous reference is
    derived from the authenticated user so the intake is still scoped.

    Phase 5: ``language`` is the user-selected language (en/si/ta). The system
    also performs best-effort script detection and resolves the final language
    (detected if confident, else selected/default). ``input_type`` is
    traceability metadata so SDG analytics can measure voice vs text usage.
    """

    session_id: str | None = Field(default=None, description="existing assessment session id")
    text: str = Field(..., min_length=1, description="patient free-text description")
    language: str | None = Field(default=None, description="user-selected language: en, si, or ta")
    input_type: str = Field(default="text", description="traceability: text or voice")


@router.post("/extract", response_model=IntakeResponse)
async def extract_intake(
    payload: IntakeExtractRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> IntakeResponse:
    user_id = current_user.id
    session_ref = payload.session_id or f"u:{user_id}"

    # If a session id is supplied, verify it exists AND belongs to the caller.
    if payload.session_id:
        from sqlalchemy import select

        stmt = select(AssessmentSessionModel).where(
            AssessmentSessionModel.id == payload.session_id
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            # Unknown session → 404 (never leak existence to other users).
            raise HTTPException(status_code=404, detail="Session not found")
        if row.user_id != user_id:
            # Cross-patient attempt → 404 (do not reveal ownership to the caller).
            raise HTTPException(status_code=404, detail="Session not found")

        # Phase 6 — persist language/input_type into session.extra_metadata
        # so population analytics can measure accessibility (SDG 3.8/10).
        # This populates an EXISTING JSON column (no schema change). Only
        # the resolved language + input_type are stored — never raw text or
        # audio. If the metadata already exists, preserve other keys.
        from app.application.ai.language import normalize_language
        resolved_lang = normalize_language(payload.language) if payload.language else "en"
        meta = dict(row.extra_metadata or {})
        meta["language"] = resolved_lang
        meta["input_type"] = input_type
        row.extra_metadata = meta
        await session.commit()

    # Phase 5 — validate language if explicitly supplied.
    if payload.language is not None and not is_supported_language(payload.language):
        raise HTTPException(
            status_code=422,
            detail="This language isn't currently supported. Please select English, Sinhala, or Tamil.",
        )

    input_type = payload.input_type if payload.input_type in ("text", "voice") else "text"

    svc = AIIntakeService(session)
    try:
        return await svc.extract(
            payload.text,
            session_ref=session_ref,
            language=payload.language,
            input_type=input_type,
        )
    except Exception as exc:  # pragma: no cover - defensive
        # Any unexpected service error → safe fallback, never a 500 that breaks
        # the intake UX. The standard questionnaire remains available.
        from app.application.dtos.intake_dtos import safe_intake_response
        from app.application.ai.intake_prompts import INTAKE_PROMPT_VERSION

        get_logger(__name__).warning("intake endpoint fallback: %s", exc)
        return safe_intake_response(
            new_trace_id_stub(),
            INTAKE_PROMPT_VERSION,
            language=payload.language or "en",
            input_type=input_type,
        )


class TranscribeResponse(BaseModel):
    """Transcription result for patient review/editing.

    The transcript is NOT fed into the clinical pipeline directly. The patient
    reviews and may edit it before submitting via ``/extract``. This ensures an
    incorrect transcript is never silently sent into clinical interpretation.
    """

    transcript: str
    language: str
    detected_language: str | None = None
    confidence: float = 0.9


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="audio recording (webm/ogg/wav/mp3)"),
    language: str = Form(default="en", description="user-selected language: en, si, or ta"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TranscribeResponse:
    """Phase 5 — transcribe audio to text (transient; never stored/logged).

    Audio is processed in-memory only and discarded immediately. The transcript
    is returned for patient review. Voice failure → 422 so the frontend can fall
    back to typing — voice never breaks the assessment system.
    """
    # Validate language.
    if not is_supported_language(language):
        raise HTTPException(
            status_code=422,
            detail="This language isn't currently supported. Please select English, Sinhala, or Tamil.",
        )
    selected = normalize_language(language)

    # Validate content type (reject unsupported audio).
    ct = (audio.content_type or "").lower()
    if ct and ct not in ACCEPTED_AUDIO_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail="Unsupported audio format. Please record in WebM, OGG, WAV, or MP3.",
        )

    # Read audio into memory (transient; never persisted).
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="No audio was captured. Please try again.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Audio recording is too long. Please try a shorter recording.",
        )

    svc = AIIntakeService(session)
    try:
        result = await svc.transcribe_audio(
            audio_bytes,
            language=selected,
            content_type=ct or "audio/webm",
        )
    except SpeechToTextError as exc:
        logger.warning("transcribe failure (safe): language=%s error=%s", selected, exc)
        raise HTTPException(
            status_code=422,
            detail="Voice input isn't available right now. You can type instead.",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("transcribe unexpected failure: %s", exc)
        raise HTTPException(
            status_code=422,
            detail="Voice input isn't available right now. You can type instead.",
        ) from exc

    return TranscribeResponse(
        transcript=result.transcript,
        language=result.language,
        detected_language=result.detected_language,
        confidence=result.confidence,
    )


class SupportedLanguage(BaseModel):
    code: str
    label: str


class LanguagesResponse(BaseModel):
    languages: list[SupportedLanguage]
    default: str


@router.get("/languages", response_model=LanguagesResponse)
async def list_languages(
    current_user=Depends(get_current_user),
) -> LanguagesResponse:
    """Phase 5 — list supported intake languages for the UI selector."""
    langs = [
        SupportedLanguage(code=code, label=LANGUAGE_LABELS[code])
        for code in SUPPORTED_INTAKE_LANGUAGES
    ]
    return LanguagesResponse(languages=langs, default=SUPPORTED_INTAKE_LANGUAGES[0])


def new_trace_id_stub() -> str:
    from app.application.dtos.intake_dtos import new_trace_id

    return new_trace_id()
