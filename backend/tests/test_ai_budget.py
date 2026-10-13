"""AI vendor spend / abuse guardrail tests.

Unit tests use an in-process FakeRedis (no server, no network). Service and
endpoint tests prove: exhaustion raises a typed 429 (never a stub fallback),
rejections are audited without PHI, and stubs bypass budgets with zero I/O.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai import ai_budget as budget_module
from app.application.ai.ai_budget import enforce_ai_budget
from app.application.ai.http_chat_provider import OpenAICompatibleChatProvider
from app.application.ai.provider import StubExplanationProvider
from app.application.services.ai_explanation_service import (
    AIExplanationService,
    _explanation_cache,
)
from app.application.services.ai_intake_service import AIIntakeService
from app.core.config import settings
from app.core.exceptions import AIBudgetExceededError
from app.infrastructure.persistence.models.ai_interaction_audit import (
    AIInteractionAuditModel,
)
from tests.test_ai_rag_phase2 import _seed_assessment

_MOCK_TOKEN = "mock-firebase-id-token"


class FakeRedis:
    """Minimal async Redis double (incr/expire/get only)."""

    def __init__(self, down: bool = False):
        self.data: dict[str, int] = {}
        self.calls = 0
        self.down = down

    async def incr(self, key: str) -> int:
        if self.down:
            raise ConnectionError("redis down")
        self.calls += 1
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    async def expire(self, key: str, ttl: int) -> bool:
        return True

    async def get(self, key: str):
        return self.data.get(key)


def _budgets(monkeypatch, *, hourly=1000, daily=1000, global_daily=1000):
    monkeypatch.setattr(settings, "ai_budget_user_hourly_requests", hourly)
    monkeypatch.setattr(settings, "ai_budget_user_daily_requests", daily)
    monkeypatch.setattr(settings, "ai_budget_global_daily_requests", global_daily)


class TestBudgetUnit:
    @pytest.mark.asyncio
    async def test_stub_calls_bypass_with_zero_io(self, monkeypatch):
        _budgets(monkeypatch, hourly=1, daily=1, global_daily=1)
        fake = FakeRedis()
        await enforce_ai_budget(
            user_id="u", operation="report_explanation", metered=False,
            redis_client=fake,
        )
        assert fake.calls == 0

    @pytest.mark.asyncio
    async def test_hourly_limit_enforced(self, monkeypatch):
        _budgets(monkeypatch, hourly=2, daily=1000, global_daily=1000)
        fake = FakeRedis()
        kw = dict(user_id="u-h", operation="report_explanation", metered=True)
        await enforce_ai_budget(redis_client=fake, **kw)
        await enforce_ai_budget(redis_client=fake, **kw)
        with pytest.raises(AIBudgetExceededError) as exc_info:
            await enforce_ai_budget(redis_client=fake, **kw)
        err = exc_info.value
        assert err.status_code == 429
        assert err.code == "ai_budget_exceeded"
        assert "hourly" in err.detail

    @pytest.mark.asyncio
    async def test_daily_and_global_limits_enforced(self, monkeypatch):
        _budgets(monkeypatch, hourly=1000, daily=1, global_daily=1000)
        fake = FakeRedis()
        await enforce_ai_budget(
            user_id="u-d", operation="intake_extract", metered=True,
            redis_client=fake,
        )
        with pytest.raises(AIBudgetExceededError):
            await enforce_ai_budget(
                user_id="u-d", operation="intake_extract", metered=True,
                redis_client=fake,
            )

        _budgets(monkeypatch, hourly=1000, daily=1000, global_daily=1)
        fake2 = FakeRedis()
        await enforce_ai_budget(
            user_id="u-g1", operation="stt_transcribe", metered=True,
            redis_client=fake2,
        )
        with pytest.raises(AIBudgetExceededError) as exc_info:
            await enforce_ai_budget(
                user_id="u-g2", operation="stt_transcribe", metered=True,
                redis_client=fake2,
            )
        assert "global" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_operations_have_independent_buckets(self, monkeypatch):
        _budgets(monkeypatch, hourly=1, daily=1000, global_daily=1000)
        fake = FakeRedis()
        await enforce_ai_budget(
            user_id="u", operation="report_explanation", metered=True,
            redis_client=fake,
        )
        # A different operation is unaffected by the exhausted bucket.
        await enforce_ai_budget(
            user_id="u", operation="intake_extract", metered=True,
            redis_client=fake,
        )

    @pytest.mark.asyncio
    async def test_disabled_tier_skipped(self, monkeypatch):
        _budgets(monkeypatch, hourly=0, daily=0, global_daily=0)
        fake = FakeRedis()
        for _ in range(5):
            await enforce_ai_budget(
                user_id="u", operation="op", metered=True, redis_client=fake
            )
        assert fake.calls == 0

    @pytest.mark.asyncio
    async def test_redis_outage_falls_back_to_local(self, monkeypatch):
        _budgets(monkeypatch, hourly=1, daily=1000, global_daily=1000)
        fake = FakeRedis(down=True)
        uid = f"local-{uuid.uuid4().hex[:8]}"
        await enforce_ai_budget(
            user_id=uid, operation="op", metered=True, redis_client=fake
        )
        with pytest.raises(AIBudgetExceededError):
            await enforce_ai_budget(
                user_id=uid, operation="op", metered=True, redis_client=fake
            )

    @pytest.mark.asyncio
    async def test_error_carries_no_secrets(self, monkeypatch):
        _budgets(monkeypatch, hourly=1, daily=1000, global_daily=1000)
        fake = FakeRedis()
        secret = "sk-SUPER-SECRET-xyz"
        monkeypatch.setattr(settings, "ai_api_key", secret)
        uid = f"sec-{uuid.uuid4().hex[:8]}"
        await enforce_ai_budget(
            user_id=uid, operation="op", metered=True, redis_client=fake
        )
        with pytest.raises(AIBudgetExceededError) as exc_info:
            await enforce_ai_budget(
                user_id=uid, operation="op", metered=True, redis_client=fake
            )
        assert secret not in str(exc_info.value)
        assert secret not in (exc_info.value.detail or "")

    def test_metered_flag(self):
        assert getattr(StubExplanationProvider(), "metered", False) is False
        provider = OpenAICompatibleChatProvider(
            base_url="https://x/v1", api_key="k", model="m"
        )
        assert provider.metered is True


class TestBudgetServiceWiring:
    @pytest.mark.asyncio
    async def test_explain_report_second_call_rejected_and_audited(
        self, db_session: AsyncSession, monkeypatch
    ):
        from tests.test_ai_providers_http import (
            _chat_client,
            _chat_ok,
            _valid_explanation,
        )

        s_id, ind_id = await _seed_assessment(db_session, "u-budget")
        _budgets(monkeypatch, hourly=1, daily=1000, global_daily=1000)
        fake = FakeRedis()
        monkeypatch.setattr(
            budget_module, "_resolve_client", lambda explicit: fake
        )
        _explanation_cache.clear()

        provider, captured = _chat_client(
            _chat_ok(_valid_explanation(ind_id)), model="gpt-4o-mini"
        )
        svc = AIExplanationService(db_session, provider=provider)
        first = await svc.explain_report(s_id, "u-budget")
        assert first.available is True
        assert len(captured["calls"]) == 1

        # A fresh (uncached) second call must be rejected by the budget.
        _explanation_cache.clear()
        with pytest.raises(AIBudgetExceededError):
            await svc.explain_report(s_id, "u-budget")
        # Vendor was NOT called again.
        assert len(captured["calls"]) == 1

        rows = (
            await db_session.execute(
                select(AIInteractionAuditModel).where(
                    AIInteractionAuditModel.session_id == s_id,
                    AIInteractionAuditModel.status == "budget_exceeded",
                )
            )
        ).scalars().all()
        assert rows, "expected a budget_exceeded audit row"
        assert rows[-1].input_context_hash is not None
        assert rows[-1].output_hash is None  # rejected before any vendor output

    @pytest.mark.asyncio
    async def test_intake_extract_passes_user_id_to_budget(
        self, db_session: AsyncSession, monkeypatch
    ):
        from tests.test_ai_intake_phase3 import _seed_graph
        from app.application.ai.intake_provider import StubClinicalIntakeProvider

        await _seed_graph(db_session, uid="budex")
        seen: dict = {}

        async def recorder(**kwargs):
            seen.update(kwargs)

        monkeypatch.setattr(
            "app.application.services.ai_intake_service.enforce_ai_budget",
            recorder,
        )
        svc = AIIntakeService(
            db_session, catalog_limit=10,
            provider=StubClinicalIntakeProvider(),
        )
        resp = await svc.extract(
            "tired on exertion", session_ref="u:budex", user_id="user-123"
        )
        assert resp.available is True
        assert seen.get("user_id") == "user-123"
        assert seen.get("operation") == "intake_extract"
        assert seen.get("metered") is False  # stub bypasses

    @pytest.mark.asyncio
    async def test_transcribe_budget_error_propagates_not_converted(
        self, db_session: AsyncSession, monkeypatch
    ):
        from app.application.ai.stt_provider import SpeechToTextError

        async def boom(**kwargs):
            raise AIBudgetExceededError(detail="over")

        monkeypatch.setattr(
            "app.application.services.ai_intake_service.enforce_ai_budget",
            boom,
        )
        svc = AIIntakeService(db_session)
        with pytest.raises(AIBudgetExceededError):
            await svc.transcribe_audio(b"audio-bytes", language="en")
        # And it is NOT a SpeechToTextError (endpoint must not 422 it).
        assert not issubclass(AIBudgetExceededError, SpeechToTextError)


class TestBudgetEndpoints:
    @pytest.mark.asyncio
    async def test_transcribe_budget_exceeded_is_429(
        self, client: AsyncClient, monkeypatch
    ):
        from app.core.exceptions import AIBudgetExceededError

        async def boom(*args, **kwargs):
            raise AIBudgetExceededError(detail="over")

        monkeypatch.setattr(
            AIIntakeService, "transcribe_audio", boom
        )
        resp = await client.post(
            "/api/v1/ai/intake/transcribe",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
            files={"audio": ("a.webm", b"fake-audio", "audio/webm")},
            data={"language": "en"},
        )
        assert resp.status_code == 429
        body = resp.json()
        text = __import__("json").dumps(body)
        assert "ai_budget_exceeded" in text

    @pytest.mark.asyncio
    async def test_extract_budget_exceeded_is_429(
        self, client: AsyncClient, monkeypatch
    ):
        async def boom(*args, **kwargs):
            from app.core.exceptions import AIBudgetExceededError

            raise AIBudgetExceededError(detail="over")

        monkeypatch.setattr(AIIntakeService, "extract", boom)
        resp = await client.post(
            "/api/v1/ai/intake/extract",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
            json={"text": "tired on exertion"},
        )
        assert resp.status_code == 429
