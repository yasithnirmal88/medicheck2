from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "DEBUG"
    secret_key: str = ""  # MUST be set via .env in production
    project_name: str = "MediCheck"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    postgres_user: str = "medicheck"
    postgres_password: str = "medicheck_secret"
    postgres_db: str = "medicheck"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    database_url: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str | None, info: dict) -> str:
        if v:
            return v
        values = info.data
        return (
            f"postgresql+asyncpg://{values.get('postgres_user', 'medicheck')}:"
            f"{values.get('postgres_password', 'medicheck_secret')}@"
            f"{values.get('postgres_host', 'localhost')}:"
            f"{values.get('postgres_port', 5432)}/"
            f"{values.get('postgres_db', 'medicheck')}"
        )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    redis_url: str | None = None

    @field_validator("redis_url", mode="before")
    @classmethod
    def validate_redis_url(cls, v: str | None, info: dict) -> str:
        if v:
            return v
        values = info.data
        password = values.get("redis_password", "")
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        db = values.get("redis_db", 0)
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    firebase_credentials_path: str | None = None
    firebase_credentials_json: str | None = None

    @property
    def firebase_credentials(self) -> dict | None:
        if self.firebase_credentials_json:
            return json.loads(self.firebase_credentials_json)
        if self.firebase_credentials_path:
            path = Path(self.firebase_credentials_path)
            if path.exists():
                return json.loads(path.read_text())
        return None

    allowed_hosts: str = "localhost,127.0.0.1,.medicheck.app"

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Security
    csrf_protection_enabled: bool = True
    rate_limit_max_requests: int = 100
    rate_limit_window_seconds: int = 60
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000
    csp_report_only: bool = False
    allow_mock_auth: bool = False  # Set to True only for local development

    celery_broker_url: str = ""
    celery_result_backend: str = ""

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def validate_celery_broker_url(cls, v: str | None, info: dict) -> str:
        if v:
            return v
        values = info.data
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        return f"redis://{host}:{port}/1"

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def validate_celery_result_backend(cls, v: str | None, info: dict) -> str:
        if v:
            return v
        values = info.data
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        return f"redis://{host}:{port}/1"

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


settings = Settings()
