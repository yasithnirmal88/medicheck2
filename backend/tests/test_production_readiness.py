"""Production readiness tests: fail-fast boot, docs gating, readiness probe,
JSON logging, and the Sentry path.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_production_readiness.py -q
"""

from __future__ import annotations

import json
import logging

import pytest
from httpx import AsyncClient

from app.core.config import Environment, Settings, settings
from app.main import _init_sentry, create_app, validate_production_boot


def _prod_settings(monkeypatch, **overrides):
    """Simulate a production environment on the global settings object."""
    monkeypatch.setattr(settings, "environment", Environment.PRODUCTION)
    # Sane production baseline; individual tests break one knob at a time.
    monkeypatch.setattr(settings, "allow_mock_auth", False)
    monkeypatch.setattr(
        settings, "firebase_credentials_json", '{"type": "service_account"}'
    )
    monkeypatch.setattr(settings, "postgres_password", "strong-prod-password")
    for key, value in overrides.items():
        monkeypatch.setattr(settings, key, value)


class TestProductionBootValidation:
    def test_non_production_never_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "environment", Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "allow_mock_auth", True)
        validate_production_boot()  # must not raise

    def test_clean_production_boots(self, monkeypatch):
        _prod_settings(monkeypatch)
        validate_production_boot()  # must not raise

    def test_mock_auth_in_production_refuses_to_boot(self, monkeypatch):
        _prod_settings(monkeypatch, allow_mock_auth=True)
        with pytest.raises(RuntimeError, match="ALLOW_MOCK_AUTH"):
            validate_production_boot()

    def test_missing_firebase_credentials_refuses_to_boot(self, monkeypatch):
        _prod_settings(monkeypatch, firebase_credentials_json=None)
        monkeypatch.setattr(settings, "firebase_credentials_path", None)
        with pytest.raises(RuntimeError, match="Firebase credentials"):
            validate_production_boot()

    def test_default_db_password_refuses_to_boot(self, monkeypatch):
        _prod_settings(monkeypatch, postgres_password="medicheck_secret")
        with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
            validate_production_boot()


class TestDocsGating:
    def test_docs_resolved_flag(self):
        assert Settings(environment="development").docs_enabled_resolved is True
        assert (
            Settings(environment="production").docs_enabled_resolved is False
        )
        assert (
            Settings(
                environment="production", docs_enabled=True
            ).docs_enabled_resolved
            is True
        )
        assert (
            Settings(
                environment="development", docs_enabled=False
            ).docs_enabled_resolved
            is False
        )

    def test_create_app_disables_docs_in_production(self, monkeypatch):
        _prod_settings(monkeypatch)
        app = create_app()
        assert app.docs_url is None
        assert app.redoc_url is None
        assert app.openapi_url is None

    def test_create_app_keeps_docs_in_development(self, monkeypatch):
        monkeypatch.setattr(settings, "environment", Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "docs_enabled", None)
        app = create_app()
        assert app.docs_url is not None


class TestReadinessProbe:
    @pytest.mark.asyncio
    async def test_ready_when_healthy(
        self, client: AsyncClient, monkeypatch
    ):
        import app.api.v1.endpoints.health as health_module

        async def healthy() -> str:
            return "healthy"

        monkeypatch.setattr(health_module, "_db_status", healthy)
        monkeypatch.setattr(health_module, "_redis_status", healthy)
        resp = await client.get("/api/v1/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_not_ready_when_dependency_down(
        self, client: AsyncClient, monkeypatch
    ):
        import app.api.v1.endpoints.health as health_module

        async def healthy() -> str:
            return "healthy"

        async def unhealthy() -> str:
            return "unhealthy"

        monkeypatch.setattr(health_module, "_db_status", healthy)
        monkeypatch.setattr(health_module, "_redis_status", unhealthy)
        resp = await client.get("/api/v1/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "not_ready"
        assert body["redis_status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_stays_200_compatible(
        self, client: AsyncClient, monkeypatch
    ):
        import app.api.v1.endpoints.health as health_module

        async def unhealthy() -> str:
            return "unhealthy"

        monkeypatch.setattr(health_module, "_db_status", unhealthy)
        monkeypatch.setattr(health_module, "_redis_status", unhealthy)
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"


class TestJsonLogging:
    def test_json_formatter_emits_structured_record(self):
        from app.core.logging import JsonFormatter

        record = logging.LogRecord(
            "medicheck.test", logging.INFO, __file__, 1, "hello %s", ("world",), None
        )
        record.request_id = "req-123"
        data = json.loads(JsonFormatter().format(record))
        assert data["message"] == "hello world"
        assert data["request_id"] == "req-123"
        assert data["level"] == "INFO"
        assert data["logger"] == "medicheck.test"
        assert "timestamp" in data


class TestSentryPath:
    def test_no_dsn_is_noop(self, monkeypatch):
        monkeypatch.setattr(settings, "sentry_dsn", "")
        assert _init_sentry() is False

    def test_missing_sdk_warns_without_crashing(self, monkeypatch):
        import importlib.util

        if importlib.util.find_spec("sentry_sdk") is not None:
            pytest.skip("sentry_sdk installed; guard path not exercisable")
        monkeypatch.setattr(settings, "sentry_dsn", "https://x@sentry.io/1")
        # sentry_sdk is intentionally NOT a hard dependency.
        assert _init_sentry() is False
