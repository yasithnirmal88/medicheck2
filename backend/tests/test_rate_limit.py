"""Rate-limit middleware tests: 429 (not 500) and proxy-aware keying."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.security.rate_limit import RateLimitMiddleware


@pytest.fixture
def limited_app() -> FastAPI:
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)
    return app


class TestRateLimitMiddleware:
    @pytest.mark.asyncio
    async def test_exceeding_limit_returns_429_not_500(self, limited_app):
        transport = ASGITransport(app=limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            assert (await c.get("/ping")).status_code == 200
            assert (await c.get("/ping")).status_code == 200
            third = await c.get("/ping")
            assert third.status_code == 429
            body = third.json()
            assert body["error"]["code"] == "rate_limit_exceeded"
            assert "Rate limit exceeded" in body["error"]["message"]
            assert int(third.headers["Retry-After"]) >= 1

    @pytest.mark.asyncio
    async def test_under_threshold_never_limited(self, limited_app):
        transport = ASGITransport(app=limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            for _ in range(2):
                assert (await c.get("/ping")).status_code == 200

    @pytest.mark.asyncio
    async def test_same_forwarded_ip_shares_bucket(self, limited_app):
        headers = {"X-Forwarded-For": "203.0.113.9"}
        transport = ASGITransport(app=limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            for _ in range(2):
                assert (await c.get("/ping", headers=headers)).status_code == 200
            assert (await c.get("/ping", headers=headers)).status_code == 429

    @pytest.mark.asyncio
    async def test_distinct_forwarded_ips_are_isolated(self, limited_app):
        transport = ASGITransport(app=limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            for ip in ("203.0.113.1", "198.51.100.2"):
                for _ in range(2):
                    resp = await c.get("/ping", headers={"X-Forwarded-For": ip})
                    assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_leftmost_forwarded_entry_is_the_key(self, limited_app):
        transport = ASGITransport(app=limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            for tail in ("198.51.100.9", "198.51.100.10"):
                resp = await c.get(
                    "/ping", headers={"X-Forwarded-For": f"203.0.113.5, {tail}"}
                )
                assert resp.status_code == 200
            third = await c.get(
                "/ping", headers={"X-Forwarded-For": "203.0.113.5, 198.51.100.11"}
            )
            assert third.status_code == 429


class TestRateLimitRealStack:
    @pytest.mark.asyncio
    async def test_real_app_exhausts_to_429_not_500(
        self, client: AsyncClient, monkeypatch
    ):
        from app.core.config import settings

        # health pings real Redis (unavailable in tests) - stub it out so the
        # full production middleware stack is exercised without network I/O.
        async def _no_redis() -> bool:
            return True

        monkeypatch.setattr(
            "app.api.v1.endpoints.health.redis_health_check", _no_redis
        )

        limit = settings.rate_limit_max_requests
        for _ in range(limit):
            assert (await client.get("/api/v1/health")).status_code == 200
        burst = await client.get("/api/v1/health")
        assert burst.status_code == 429
        assert burst.json()["error"]["code"] == "rate_limit_exceeded"
        assert burst.headers.get("Retry-After")
