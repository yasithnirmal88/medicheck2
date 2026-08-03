from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table

from app.infrastructure.database import Base

user_role_table = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        String(32),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
