from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.infrastructure.database import Base


def resolve_audit_schema(database_url: str | None = None) -> str | None:
    """PostgreSQL schema for high-volume audit tables.

    Returns ``"audit"`` on PostgreSQL, ``None`` elsewhere. SQLite has no
    schemas, so audit tables live in the default namespace there — this
    keeps ``Base.metadata.create_all`` (tests, local dev) behaving exactly
    as before while production PostgreSQL gets physical separation.
    Pure function of the URL so the branching is unit-testable.
    """
    from app.core.config import settings

    url = database_url if database_url is not None else settings.database_url
    return "audit" if url.startswith(("postgresql", "postgres")) else None


#: Schema qualifier applied (via ``__table_args__``) to audit tables that
#: must never share hot clinical-table storage. ``None`` on SQLite.
AUDIT_SCHEMA = resolve_audit_schema()


class UUIDPrimaryKeyMixin:
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        sort_order=-100,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=100,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=101,
        index=True,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        sort_order=102,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
