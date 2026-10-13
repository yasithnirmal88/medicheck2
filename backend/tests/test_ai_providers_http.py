"""Real-provider path tests: OpenAI-compatible LLM + STT over mocked HTTP.

No network, no API keys, no live vendor calls:

- ``httpx.MockTransport`` simulates the vendor for every HTTP-path test.
- Settings are patched with ``monkeypatch`` (auto-reverted per test).
- End-to-end flows run through the real service layer
  (``AIExplanationService`` with RAG + validation + audit,
  ``AIIntakeService`` extraction + STT transcription).

Also covers: fail-fast selection (unknown names / missing credentials raise
``AIConfigurationError`` — never silent stub fallback), error mapping
(provider-down / invalid output), the output-side diagnostic screen, audit
metadata without PHI, and the RBAC-gated ``GET /api/v1/ai/health`` endpoint.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.http_chat_provider import OpenAICompatibleChatProvider
from app.application.ai.http_stt_provider import OpenAICompatibleSTTProvider
from app.application.ai.intake_provider import (
    AIIntakeProviderError,
    get_intake_provider,
)
from app.application.ai.longitudinal_provider import (
    AIProviderError as LongitudinalProviderError,
)
from app.application.ai.longitudinal_provider import get_longitudinal_provider
from app.application.ai.personalized_provider import PersonalizedExplanationProvider
from app.application.ai.provider import (
    AIProviderError,
    StubExplanationProvider,
    get_explanation_provider,
)
from app.application.ai.provider_selection import (
    resolve_llm_config,
    resolve_stt_config,
)
from app.application.ai.queue_ranking_provider import (
    StubQueueRankingProvider,
    get_queue_ranking_provider,
)
from app.application.ai.stt_provider import (
    SpeechToTextError,
    StubSpeechToTextProvider,
    get_stt_provider,
)
from app.application.dtos.ai_dtos import screen_diagnostic_claims
from app.application.services.ai_explanation_service import (
    AIExplanationService,
    _explanation_cache,
)
from app.application.services.ai_intake_service import AIIntakeService
from app.core.config import settings
from app.core.exceptions import AIConfigurationError
from app.core.security.rbac import Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.ai_interaction_audit import (
    AIInteractionAuditModel,
)
from tests.test_ai_intake_phase3 import _seed_graph
from tests.test_ai_rag_phase2 import _seed_assessment

_MOCK_TOKEN = "mock-firebase-id-token"
_SECRET = "SECRET-KEY-SENTINEL-9f8e"


# ---------------------------------------------------------------------------
# Helpers: mocked vendor transports
# ---------------------------------------------------------------------------


def _chat_client(handler, *, calls: dict | None = None, model: str = "test-model"):
    """Build an OpenAICompatibleChatProvider over a MockTransport handler."""
    captured: dict = {"calls": calls if calls is not None else []}

    def wrapped(request: httpx.Request) -> httpx.Response:
        captured["calls"].append(request)
        return handler(request)

    transport = httpx.MockTransport(wrapped)
    client = httpx.AsyncClient(transport=transport)
    provider = OpenAICompatibleChatProvider(
        base_url="https://llm.test/v1",
        api_key="test-key",
        model=model,
        timeout_seconds=5.0,
        max_retries=1,
        http_client=client,
    )
    return provider, captured


def _chat_ok(content: str, *, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status, json={"choices": [{"message": {"content": content}}]}
        )

    return handler


def _stt_client(handler):
    captured: dict = {"calls": []}

    def wrapped(request: httpx.Request) -> httpx.Response:
        captured["calls"].append(request)
        return handler(request)

    transport = httpx.MockTransport(wrapped)
    client = httpx.AsyncClient(transport=transport)
    provider = OpenAICompatibleSTTProvider(
        base_url="https://stt.test/v1",
        api_key="test-key",
        model="whisper-1",
        timeout_seconds=5.0,
        max_retries=1,
        http_client=client,
    )
    return provider, captured


def _valid_explanation(ind_id: str) -> str:
    return json.dumps(
        {
            "summary": "Assessment signals explained without diagnosing.",
            "key_findings": [
                {
                    "title": "Finding",
                    "explanation": "A signal from the assessment answers.",
                    "source_indicator_ids": [ind_id],
                    "evidence_ids": [],
                }
            ],
            "severity_explanation": "What the reported category means.",
            "recommendation_explanations": [],
            "evidence_notes": [
                "No supporting evidence was available from the MediCheck "
                "evidence repository for this explanation."
            ],
            "limitations": "Cannot conclude more than the assessment found.",
            "disclaimer": (
                "This AI-generated explanation is based on your MediCheck "
                "assessment and does not constitute a diagnosis."
            ),
        }
    )


def _research_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4().hex,
        firebase_uid="test-research-uid",
        email="research@example.com",
        full_name="Research Reviewer",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles={Role.RESEARCH_REVIEWER},
        last_login_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


# ---------------------------------------------------------------------------
# Selection: safe defaults + fail-fast
# ---------------------------------------------------------------------------


class TestProviderSelection:
    def test_defaults_are_stubs(self):
        assert isinstance(get_explanation_provider(), StubExplanationProvider)
        assert type(get_intake_provider()).__name__ == "StubClinicalIntakeProvider"
        assert type(get_longitudinal_provider()).__name__ == "StubLongitudinalProvider"
        assert isinstance(get_stt_provider(), StubSpeechToTextProvider)
        assert isinstance(get_queue_ranking_provider(), StubQueueRankingProvider)

    def test_personalized_stub_mapping(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "personalized-stub")
        assert isinstance(get_explanation_provider(), PersonalizedExplanationProvider)
        # personalized-stub is explanation-scoped: intake/longitudinal keep
        # their own deterministic stubs (no raise — a known stub name).
        assert type(get_intake_provider()).__name__ == "StubClinicalIntakeProvider"
        assert (
            type(get_longitudinal_provider()).__name__ == "StubLongitudinalProvider"
        )

    def test_unknown_llm_name_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "bogus-vendor")
        with pytest.raises(AIConfigurationError):
            get_explanation_provider()
        with pytest.raises(AIConfigurationError):
            get_intake_provider()
        with pytest.raises(AIConfigurationError):
            get_longitudinal_provider()

    def test_unknown_stt_name_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "stt_provider", "bogus-stt")
        with pytest.raises(AIConfigurationError):
            get_stt_provider()

    def test_unknown_queue_name_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "chw_queue_provider", "bogus-queue")
        with pytest.raises(AIConfigurationError):
            get_queue_ranking_provider()

    def test_openai_missing_key_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "openai")
        monkeypatch.setattr(settings, "ai_api_key", "")
        monkeypatch.setattr(settings, "ai_model", "gpt-4o-mini")
        with pytest.raises(AIConfigurationError) as exc_info:
            get_explanation_provider()
        assert "AI_API_KEY" in str(exc_info.value)

    def test_openai_missing_model_raises_without_leaking_key(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "openai")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        monkeypatch.setattr(settings, "ai_model", "")
        with pytest.raises(AIConfigurationError) as exc_info:
            get_explanation_provider()
        assert "AI_MODEL" in str(exc_info.value)
        assert _SECRET not in str(exc_info.value)

    def test_openai_full_config_builds_http_provider(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "openai")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        monkeypatch.setattr(settings, "ai_model", "gpt-4o-mini")
        provider = get_explanation_provider()
        assert isinstance(provider, OpenAICompatibleChatProvider)
        assert provider.model == "gpt-4o-mini"
        # Default base URL + configured timeout/retries flow through.
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.timeout_seconds == settings.ai_request_timeout_seconds

    def test_openai_compatible_alias(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "openai-compatible")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        monkeypatch.setattr(settings, "ai_model", "m")
        assert isinstance(
            get_explanation_provider(), OpenAICompatibleChatProvider
        )
        assert isinstance(get_intake_provider(), OpenAICompatibleChatProvider)
        assert isinstance(
            get_longitudinal_provider(), OpenAICompatibleChatProvider
        )

    def test_custom_base_url_honored(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_provider", "openai-compatible")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        monkeypatch.setattr(settings, "ai_model", "m")
        monkeypatch.setattr(settings, "ai_base_url", "https://gateway.local/v1/")
        provider = get_explanation_provider()
        assert provider.base_url == "https://gateway.local/v1"

    def test_stt_whisper_name_and_default_model(self, monkeypatch):
        monkeypatch.setattr(settings, "stt_provider", "whisper")
        monkeypatch.setattr(settings, "stt_api_key", _SECRET)
        monkeypatch.setattr(settings, "stt_model", "")
        provider = get_stt_provider()
        assert isinstance(provider, OpenAICompatibleSTTProvider)
        assert provider.model == "whisper-1"

    def test_stt_missing_key_raises_without_leaking(self, monkeypatch):
        monkeypatch.setattr(settings, "stt_provider", "openai")
        monkeypatch.setattr(settings, "stt_api_key", "")
        with pytest.raises(AIConfigurationError) as exc_info:
            get_stt_provider()
        assert "STT_API_KEY" in str(exc_info.value)

    def test_resolve_helpers_reject_stubs_and_unknowns(self):
        with pytest.raises(AIConfigurationError):
            resolve_llm_config("stub")
        with pytest.raises(AIConfigurationError):
            resolve_llm_config("nope")
        with pytest.raises(AIConfigurationError):
            resolve_stt_config("stub")
        with pytest.raises(AIConfigurationError):
            resolve_stt_config("nope")


# ---------------------------------------------------------------------------
# HTTP chat provider: protocol, retries, robustness
# ---------------------------------------------------------------------------


class TestOpenAIChatProvider:
    @pytest.mark.asyncio
    async def test_explain_posts_chat_completions(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, captured = _chat_client(_chat_ok('{"a": 1}'))
        raw = await provider.explain(ReportExplanationContext())
        assert json.loads(raw) == {"a": 1}
        (request,) = captured["calls"]
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content.decode())
        assert body["model"] == "test-model"
        assert body["temperature"] == 0
        assert body["response_format"] == {"type": "json_object"}
        # The non-diagnostic system prompt is actually sent to the vendor.
        assert "NOT a diagnostic engine" in body["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_retry_then_success(self):
        calls = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(500, json={"error": "busy"})
            return httpx.Response(
                200, json={"choices": [{"message": {"content": '{"a": 1}'}}]}
            )

        provider, _ = _chat_client(handler)
        from app.application.dtos.ai_dtos import ReportExplanationContext

        raw = await provider.explain(ReportExplanationContext())
        assert json.loads(raw) == {"a": 1}
        assert calls["n"] == 2

    @pytest.mark.asyncio
    async def test_persistent_500_raises(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, captured = _chat_client(
            lambda request: httpx.Response(500, json={"error": "down"})
        )
        with pytest.raises(AIProviderError):
            await provider.explain(ReportExplanationContext())
        assert len(captured["calls"]) == 2  # initial + 1 retry

    @pytest.mark.asyncio
    async def test_401_fails_immediately_without_retry(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, captured = _chat_client(
            lambda request: httpx.Response(401, json={"error": "bad key"})
        )
        with pytest.raises(AIProviderError):
            await provider.explain(ReportExplanationContext())
        assert len(captured["calls"]) == 1

    @pytest.mark.asyncio
    async def test_transport_error_raises(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        provider, _ = _chat_client(handler)
        with pytest.raises(AIProviderError):
            await provider.explain(ReportExplanationContext())

    @pytest.mark.asyncio
    async def test_fenced_json_is_stripped(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, _ = _chat_client(_chat_ok('```json\n{"a": 1}\n```'))
        raw = await provider.explain(ReportExplanationContext())
        assert json.loads(raw) == {"a": 1}

    @pytest.mark.asyncio
    async def test_empty_choices_raises(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, _ = _chat_client(lambda request: httpx.Response(200, json={"choices": []}))
        with pytest.raises(AIProviderError):
            await provider.explain(ReportExplanationContext())

    @pytest.mark.asyncio
    async def test_non_json_body_raises(self):
        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider, _ = _chat_client(
            lambda request: httpx.Response(200, content=b"not json")
        )
        with pytest.raises(AIProviderError):
            await provider.explain(ReportExplanationContext())

    @pytest.mark.asyncio
    async def test_intake_error_maps_to_intake_error(self):
        from app.application.dtos.intake_dtos import IntakeRequestContext
        from tests.test_ai_intake_phase3 import _entry
        from app.application.dtos.intake_dtos import IndicatorCatalog

        provider, _ = _chat_client(
            lambda request: httpx.Response(500, json={"error": "down"})
        )
        ctx = IntakeRequestContext(
            session_ref="u:t",
            patient_message="hello",
            catalog=IndicatorCatalog(entries=[_entry("i1", "X")]),
            prompt_version="1.0",
        )
        with pytest.raises(AIIntakeProviderError):
            await provider.extract_candidates(ctx)

    @pytest.mark.asyncio
    async def test_trajectory_error_maps_to_longitudinal_error(self):
        from app.application.dtos.longitudinal_dtos import (
            LongitudinalExplanationContext,
        )

        provider, _ = _chat_client(
            lambda request: httpx.Response(500, json={"error": "down"})
        )
        with pytest.raises(LongitudinalProviderError):
            await provider.explain_trajectory(LongitudinalExplanationContext())

    @pytest.mark.asyncio
    async def test_api_key_never_logged(self, caplog):
        import logging

        from app.application.dtos.ai_dtos import ReportExplanationContext

        provider = OpenAICompatibleChatProvider(
            base_url="https://llm.test/v1",
            api_key=_SECRET,
            model="m",
            max_retries=0,
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(500, json={})
                )
            ),
        )
        with caplog.at_level(logging.WARNING):
            with pytest.raises(AIProviderError):
                await provider.explain(ReportExplanationContext())
        assert _SECRET not in caplog.text


# ---------------------------------------------------------------------------
# HTTP STT provider
# ---------------------------------------------------------------------------


class TestOpenAISttProvider:
    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/audio/transcriptions"
            assert request.headers["authorization"] == "Bearer test-key"
            return httpx.Response(200, json={"text": "I feel dizzy sometimes"})

        provider, captured = _stt_client(handler)
        result = await provider.transcribe(
            b"fake-audio-bytes", language="en", content_type="audio/webm"
        )
        assert result.transcript == "I feel dizzy sometimes"
        assert result.language == "en"
        assert len(captured["calls"]) == 1

    @pytest.mark.asyncio
    async def test_empty_and_oversize_audio_rejected_without_http(self):
        from app.application.ai.stt_provider import MAX_AUDIO_BYTES

        provider, captured = _stt_client(
            lambda request: httpx.Response(200, json={"text": "x"})
        )
        with pytest.raises(SpeechToTextError):
            await provider.transcribe(b"")
        with pytest.raises(SpeechToTextError):
            await provider.transcribe(b"x" * (MAX_AUDIO_BYTES + 1))
        assert captured["calls"] == []

    @pytest.mark.asyncio
    async def test_401_raises_without_retry(self):
        provider, captured = _stt_client(
            lambda request: httpx.Response(401, json={"error": "bad key"})
        )
        with pytest.raises(SpeechToTextError):
            await provider.transcribe(b"audio")
        assert len(captured["calls"]) == 1

    @pytest.mark.asyncio
    async def test_500_retry_then_success(self):
        calls = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(500, json={"error": "busy"})
            return httpx.Response(200, json={"text": "ok"})

        provider, _ = _stt_client(handler)
        result = await provider.transcribe(b"audio")
        assert result.transcript == "ok"
        assert calls["n"] == 2

    @pytest.mark.asyncio
    async def test_empty_transcript_raises(self):
        provider, _ = _stt_client(
            lambda request: httpx.Response(200, json={"text": "   "})
        )
        with pytest.raises(SpeechToTextError):
            await provider.transcribe(b"audio")

    @pytest.mark.asyncio
    async def test_transport_error_raises(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("down")

        provider, _ = _stt_client(handler)
        with pytest.raises(SpeechToTextError):
            await provider.transcribe(b"audio")


# ---------------------------------------------------------------------------
# Diagnostic screen (output-side, negation-aware)
# ---------------------------------------------------------------------------


class TestDiagnosticScreen:
    def test_explicit_claims_rejected(self):
        for text in (
            "You have type 2 diabetes.",
            "You were diagnosed with hypertension.",
            "This confirms a confirmed diagnosis of asthma.",
            "Your disease is progressing and will develop further.",
        ):
            with pytest.raises(ValueError):
                screen_diagnostic_claims(text)

    def test_negated_and_safe_phrasing_passes(self):
        for text in (
            "This does not mean you have a disease.",
            "These are assessment signals, not confirmed diagnoses.",
            "AI did not diagnose a disease, calculate your clinical score, "
            "determine severity, create your recommendations, or modify "
            "your assessment.",
            "This AI-generated explanation is based on your MediCheck "
            "assessment and does not constitute a diagnosis.",
            "Your assessment flagged 2 finding(s) across: heart. Possible "
            "condition(s) considered by the engine: none.",
        ):
            screen_diagnostic_claims(text)  # must not raise


class TestMultilingualDiagnosticScreen:
    """Sinhala + Tamil claim screening (subject+verb forms, negation hatch).

    Claim sentences use the canonical "you have X" / "confirmed" forms an
    LLM emits; negated forms mirror the repo's own disclaimer phrasing.
    """

    def test_sinhala_claims_rejected(self):
        for text in (
            "ඔබට දියවැඩියාව තියෙනවා.",
            "ඔබට අධි රුධිර පීඩනය තහවුරුයි.",
            "ඔබට පිළිකාවක් ඇති බව තහවුරුයි.",
        ):
            with pytest.raises(ValueError):
                screen_diagnostic_claims(text)

    def test_sinhala_negated_claims_pass(self):
        for text in (
            "ඔබට දියවැඩියාව තියෙනවා නොවේ.",
            "මෙය ඔබට රෝගය ඇත බව නොකියයි.",
            "ඔබට කිසිම රෝගයක් නැහැ.",
        ):
            screen_diagnostic_claims(text)  # must not raise

    def test_tamil_claims_rejected(self):
        for text in (
            "உங்களுக்கு நீரிழிவு உள்ளது.",
            "உங்கள் நோய் உறுதி செய்யப்பட்டது.",
            "உங்களுக்கு இரத்த அழுத்தம் இருக்கிறது.",
        ):
            with pytest.raises(ValueError):
                screen_diagnostic_claims(text)

    def test_tamil_negated_claims_pass(self):
        for text in (
            "உங்களுக்கு நீரிழிவு உள்ளது அல்ல.",
            "இந்த விளக்கம் உங்களுக்கு நோய் உள்ளது எனச் சொல்லாது.",
            "உங்களுக்கு எந்த நோயும் இல்லை.",
        ):
            screen_diagnostic_claims(text)  # must not raise

    def test_bare_existential_verbs_are_not_claims(self):
        # "have/exists" without the "you" subject is innocuous (e.g. asking
        # the patient a question), in all three languages.
        for text in (
            "Any questions about these findings?",
            "ප්‍රශ්න තියෙනවා නම් අසන්න.",
            "கேள்விகள் இருந்தால் கேளுங்கள்.",
        ):
            screen_diagnostic_claims(text)  # must not raise

    def test_romanized_sinhala_tamil_not_covered(self):
        """Documents a residual gap: Latin-script Sinhala/Tamil evades the
        native-script patterns and relies on prompt binding + allow-lists."""
        screen_diagnostic_claims("oyata diabetes thiyenawa.")  # must not raise

    def test_shipped_stub_strings_pass_the_screen(self):
        """Every patient-facing SI/TA/EN string in the AI phrase tables and
        intake clarifications must survive the screen (false-positive guard).
        """
        from app.application.ai.intake_provider import _localized_clarification
        from app.application.ai.personalized_provider import _PHRASES

        corpus: list[str] = []
        for table in _PHRASES.values():
            corpus.extend(table.values())
        for lang in ("en", "si", "ta"):
            corpus.append(_localized_clarification(lang))
        assert len(corpus) >= 10, "expected a non-trivial stub corpus"
        for text in corpus:
            screen_diagnostic_claims(text)  # must not raise


# ---------------------------------------------------------------------------
# End-to-end: report explanation over mocked HTTP (RAG + validation + audit)
# ---------------------------------------------------------------------------


class TestHttpExplanationEndToEnd:
    @pytest.mark.asyncio
    async def test_valid_http_explanation(
        self, db_session: AsyncSession, monkeypatch
    ):
        s_id, ind_id = await _seed_assessment(db_session, "u-http-ok")
        monkeypatch.setattr(settings, "ai_provider", "openai")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        monkeypatch.setattr(settings, "ai_model", "gpt-4o-mini")
        _explanation_cache.clear()

        provider, captured = _chat_client(
            _chat_ok(_valid_explanation(ind_id)), model="gpt-4o-mini"
        )
        svc = AIExplanationService(db_session, provider=provider)
        resp = await svc.explain_report(s_id, "u-http-ok")

        assert resp.available is True
        assert resp.provider == "openai-compatible"
        assert resp.model == "gpt-4o-mini"
        assert resp.key_findings[0].evidence_ids == []
        # Vendor received the grounded context (allow-listed ids only).
        body = json.loads(captured["calls"][0].content.decode())
        assert ind_id in body["messages"][1]["content"]

        rows = (
            await db_session.execute(
                select(AIInteractionAuditModel).where(
                    AIInteractionAuditModel.session_id == s_id
                )
            )
        ).scalars().all()
        assert rows, "expected an audit record for the HTTP explanation"
        row = rows[-1]
        assert row.provider == "openai-compatible"
        assert row.model == "gpt-4o-mini"
        assert row.input_context_hash and row.output_hash
        # Audit stores hashes + ids only — no free-text PHI columns exist.
        cols = {c.name for c in AIInteractionAuditModel.__table__.columns}
        assert not (
            cols
            & {
                "transcript",
                "raw_output",
                "raw_response",
                "prompt_text",
                "audio",
                "patient_message",
                "message",
            }
        )

    @pytest.mark.asyncio
    async def test_http_hallucinated_id_rejected(self, db_session: AsyncSession):
        s_id, ind_id = await _seed_assessment(db_session, "u-http-bad")
        _explanation_cache.clear()
        raw = json.dumps(
            {
                "summary": "bad",
                "key_findings": [
                    {
                        "title": "f",
                        "explanation": "e",
                        "source_indicator_ids": ["FAKE-IND-ID"],
                        "evidence_ids": [],
                    }
                ],
                "recommendation_explanations": [],
                "evidence_notes": [],
                "limitations": "l",
                "disclaimer": "This AI-generated explanation is based on your "
                "MediCheck assessment and does not constitute a diagnosis.",
            }
        )
        provider, _ = _chat_client(_chat_ok(raw))
        svc = AIExplanationService(db_session, provider=provider)
        resp = await svc.explain_report(s_id, "u-http-bad")
        assert resp.available is False

    @pytest.mark.asyncio
    async def test_http_diagnostic_claim_rejected(self, db_session: AsyncSession):
        s_id, ind_id = await _seed_assessment(db_session, "u-http-dx")
        _explanation_cache.clear()
        raw = json.dumps(
            {
                "summary": "You have type 2 diabetes based on your results.",
                "key_findings": [
                    {
                        "title": "f",
                        "explanation": "A signal from the assessment.",
                        "source_indicator_ids": [ind_id],
                        "evidence_ids": [],
                    }
                ],
                "recommendation_explanations": [],
                "evidence_notes": [],
                "limitations": "l",
                "disclaimer": "This AI-generated explanation is based on your "
                "MediCheck assessment and does not constitute a diagnosis.",
            }
        )
        provider, _ = _chat_client(_chat_ok(raw))
        svc = AIExplanationService(db_session, provider=provider)
        resp = await svc.explain_report(s_id, "u-http-dx")
        # Diagnostic claim → validation failure → safe fallback.
        assert resp.available is False
        assert resp.quality_status.value == "validation_failed"

    @pytest.mark.asyncio
    async def test_http_provider_down_falls_back(self, db_session: AsyncSession):
        s_id, _ = await _seed_assessment(db_session, "u-http-down")
        _explanation_cache.clear()

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("vendor down")

        provider, _ = _chat_client(handler)
        svc = AIExplanationService(db_session, provider=provider)
        resp = await svc.explain_report(s_id, "u-http-down")
        assert resp.available is False
        assert resp.quality_status.value == "provider_unavailable"


# ---------------------------------------------------------------------------
# End-to-end: intake extraction + STT over mocked HTTP
# ---------------------------------------------------------------------------


class TestHttpIntakeEndToEnd:
    @pytest.mark.asyncio
    async def test_http_intake_extraction(self, db_session: AsyncSession):
        _, ind_id, _, _ = await _seed_graph(db_session, uid="httpin")
        raw = json.dumps(
            {
                "observations": [
                    {
                        "source_text": "tired on exertion",
                        "normalized_concept": "fatigue",
                    }
                ],
                "candidates": [
                    {
                        "indicator_id": ind_id,
                        "confidence": 0.8,
                        "observation_ids": ["tired on exertion"],
                        "reason": "Patient words match the indicator name.",
                    }
                ],
            }
        )
        provider, captured = _chat_client(_chat_ok(raw))
        svc = AIIntakeService(db_session, catalog_limit=10, provider=provider)
        resp = await svc.extract("tired on exertion", session_ref="u:httpin")
        assert resp.available is True
        assert any(c.indicator_id == ind_id for c in resp.candidate_indicators)
        # Vendor received patient text + bounded catalog (ids only citable).
        body = json.loads(captured["calls"][0].content.decode())
        assert "tired on exertion" in body["messages"][1]["content"]
        assert ind_id in body["messages"][1]["content"]

    @pytest.mark.asyncio
    async def test_http_intake_failure_falls_back(self, db_session: AsyncSession):
        await _seed_graph(db_session, uid="httpfail")

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("vendor down")

        provider, _ = _chat_client(handler)
        svc = AIIntakeService(db_session, catalog_limit=10, provider=provider)
        resp = await svc.extract("tired on exertion", session_ref="u:httpfail")
        assert resp.available is False

    @pytest.mark.asyncio
    async def test_http_stt_transcription_through_service(
        self, db_session: AsyncSession
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/audio/transcriptions"
            return httpx.Response(200, json={"text": "I feel dizzy sometimes"})

        stt, _ = _stt_client(handler)
        svc = AIIntakeService(db_session, stt_provider=stt)
        result = await svc.transcribe_audio(
            b"fake-audio-bytes", language="en", content_type="audio/webm"
        )
        assert result.transcript == "I feel dizzy sometimes"
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_http_stt_failure_raises_for_endpoint_fallback(
        self, db_session: AsyncSession
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("stt down")

        stt, _ = _stt_client(handler)
        svc = AIIntakeService(db_session, stt_provider=stt)
        with pytest.raises(SpeechToTextError):
            await svc.transcribe_audio(b"fake-audio-bytes", language="en")


# ---------------------------------------------------------------------------
# Health endpoint + probe
# ---------------------------------------------------------------------------


class TestAIHealthEndpoint:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ai/health")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_reports_stub_defaults_without_probe(
        self, client: AsyncClient, monkeypatch
    ):
        from app.api.deps import get_ai_governance_user

        monkeypatch.setattr(settings, "ai_provider", "stub")
        monkeypatch.setattr(settings, "stt_provider", "stub")
        monkeypatch.setattr(settings, "ai_api_key", "")
        app = client._transport.app  # type: ignore[attr-defined]
        app.dependency_overrides[get_ai_governance_user] = _research_user
        try:
            resp = await client.get(
                "/api/v1/ai/health",
                headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["explanation"]["implementation"] == "StubExplanationProvider"
            assert data["stt"]["implementation"] == "StubSpeechToTextProvider"
            assert data["explanation"]["probe"] == "not_run"
            assert data["explanation"]["credentials_present"] is False
        finally:
            app.dependency_overrides.pop(get_ai_governance_user, None)

    @pytest.mark.asyncio
    async def test_misconfigured_name_reported_not_raised(
        self, client: AsyncClient, monkeypatch
    ):
        from app.api.deps import get_ai_governance_user

        monkeypatch.setattr(settings, "ai_provider", "bogus-vendor")
        monkeypatch.setattr(settings, "ai_api_key", _SECRET)
        app = client._transport.app  # type: ignore[attr-defined]
        app.dependency_overrides[get_ai_governance_user] = _research_user
        try:
            resp = await client.get(
                "/api/v1/ai/health",
                headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["explanation"]["implementation"] == "misconfigured"
            assert "AI_PROVIDER" in (data["explanation"]["error"] or "")
            # Secret material never appears in the response.
            assert _SECRET not in resp.text
        finally:
            app.dependency_overrides.pop(get_ai_governance_user, None)

    def test_probe_base_healthy(self, monkeypatch):
        from app.api.v1.endpoints import ai_health

        def fake_get(url, **kwargs):
            assert url.endswith("/models")
            auth = {k.lower(): v for k, v in kwargs["headers"].items()}
            assert auth["authorization"] == "Bearer k"
            return httpx.Response(200, json={"data": []})

        monkeypatch.setattr(httpx, "get", fake_get)
        assert ai_health._probe_base("https://x/v1", "k") == "healthy"

    def test_probe_base_auth_failed(self, monkeypatch):
        from app.api.v1.endpoints import ai_health

        monkeypatch.setattr(
            httpx, "get", lambda url, **kw: httpx.Response(401, json={})
        )
        assert ai_health._probe_base("https://x/v1", "k") == "auth_failed"

    def test_probe_base_unreachable(self, monkeypatch):
        from app.api.v1.endpoints import ai_health

        def fake_get(url, **kwargs):
            raise httpx.ConnectError("down")

        monkeypatch.setattr(httpx, "get", fake_get)
        assert ai_health._probe_base("https://x/v1", "k") == "unreachable"
