"""Identity-owned read API for user rows.

Lets other bounded contexts consume basic user data WITHOUT importing
``UserModel`` (or any persistence internals) directly. All functions take an
``AsyncSession`` and return plain-Python data (frozen DTOs / sets), so a
future extraction of Identity behind HTTP only changes these bodies —
call sites keep their shape.

Semantics mirror ``session.get``: lookups include soft-deleted and inactive
rows; callers apply ``is_active`` / ``is_deleted`` to match the filtering
the query they replace used to do. ``get_active_user_ids`` is the
pre-filtered variant for analytics-style cohort queries.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.user import UserModel


class UserSummary(BaseModel):
    """Minimal, display-safe user snapshot for cross-context reads."""

    model_config = ConfigDict(frozen=True)

    id: str
    full_name: str
    email: str
    is_active: bool
    is_deleted: bool


def _to_summary(
    user_id: str,
    full_name: str | None,
    email: str | None,
    is_active: bool | None,
    deleted_at: object | None,
) -> UserSummary:
    return UserSummary(
        id=user_id,
        full_name=full_name or "",
        email=email or "",
        is_active=bool(is_active),
        is_deleted=deleted_at is not None,
    )


async def get_user_summaries(
    session: AsyncSession, user_ids: set[str] | list[str]
) -> dict[str, UserSummary]:
    """Batch-load user summaries keyed by user id (single round-trip).

    Returns an entry per found row; unknown ids are simply absent (same as
    ``session.get`` returning ``None``). Deleted/inactive rows ARE included —
    filter on ``is_active`` / ``is_deleted`` to preserve the semantics of the
    query being replaced.
    """
    ids = set(user_ids)
    if not ids:
        return {}
    stmt = select(
        UserModel.id,
        UserModel.full_name,
        UserModel.email,
        UserModel.is_active,
        UserModel.deleted_at,
    ).where(UserModel.id.in_(ids))
    out: dict[str, UserSummary] = {}
    for row in (await session.execute(stmt)).all():
        out[row[0]] = _to_summary(row[0], row[1], row[2], row[3], row[4])
    return out


async def get_user_summary(
    session: AsyncSession, user_id: str
) -> UserSummary | None:
    """Load one user summary (``None`` when the row does not exist)."""
    summaries = await get_user_summaries(session, {user_id})
    return summaries.get(user_id)


async def get_user_ids(
    session: AsyncSession, *, active_only: bool = True
) -> set[str]:
    """Ids of non-deleted users for cohort filtering.

    ``active_only=True`` (default) additionally requires ``is_active`` —
    this matches the canonical analytics cohort filter. Pass
    ``active_only=False`` for the legacy deleted-only semantics some
    distribution queries use. Both variants exist to preserve each call
    site's exact filtering; new code should prefer ``active_only=True``.
    """
    stmt = select(UserModel.id).where(UserModel.deleted_at.is_(None))
    if active_only:
        stmt = stmt.where(UserModel.is_active.is_(True))
    return set((await session.execute(stmt)).scalars().all())
