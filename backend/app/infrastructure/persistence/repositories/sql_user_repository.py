from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.role import RoleModel


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._model = UserModel

    def _base_query(self):
        return select(UserModel).options(selectinload(UserModel.roles))

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            email_verified=user.email_verified,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )
        
        # Fetch and associate roles if user has any
        if user.roles:
            role_codes = list(user.roles)
            stmt = select(RoleModel).where(RoleModel.code.in_(role_codes))
            result = await self._session.execute(stmt)
            roles = list(result.scalars().all())
            
            # Create missing roles if they don't exist
            existing_codes = {r.code for r in roles}
            for code in role_codes:
                if code not in existing_codes:
                    new_role = RoleModel(
                        code=code,
                        name={"en": code.replace("_", " ").title()},
                        description=f"System role: {code}",
                        is_system=True,
                        priority=0,
                    )
                    self._session.add(new_role)
                    roles.append(new_role)
            
            model.roles = roles
        
        self._session.add(model)
        await self._session.flush()
        
        # When creating a new user, return entity with roles from the User object
        # since model.roles might not be populated yet due to flush timing
        return User(
            id=model.id,
            firebase_uid=model.firebase_uid,
            email=model.email,
            full_name=model.full_name,
            avatar_url=model.avatar_url,
            email_verified=model.email_verified,
            is_active=model.is_active,
            roles=user.roles,  # Use roles from the input User object
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    async def find_by_id(self, id: str) -> User | None:
        stmt = self._base_query().where(UserModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_firebase_uid(self, uid: str) -> User | None:
        stmt = self._base_query().where(UserModel.firebase_uid == uid)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_email(self, email: str) -> User | None:
        stmt = self._base_query().where(UserModel.email == email.lower().strip())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> User:
        stmt = self._base_query().where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User with id {user.id} not found")

        model.firebase_uid = user.firebase_uid
        model.email = user.email
        model.full_name = user.full_name
        model.avatar_url = user.avatar_url
        model.email_verified = user.email_verified
        model.is_active = user.is_active
        model.last_login_at = user.last_login_at
        model.updated_at = user.updated_at
        model.deleted_at = user.deleted_at

        await self._session.flush()
        return user

    async def delete(self, id: str) -> None:
        stmt = self._base_query().where(UserModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[User]:
        stmt = self._base_query().offset(skip).limit(limit)
        if not include_deleted:
            stmt = stmt.where(UserModel.deleted_at.is_(None))
        stmt = stmt.order_by(UserModel.created_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count(self, include_deleted: bool = False) -> int:
        stmt = select(func.count(UserModel.id))
        if not include_deleted:
            stmt = stmt.where(UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    def _to_entity(self, model: UserModel, is_new: bool = False) -> User:
        roles = set()
        if not is_new and hasattr(model, "roles") and model.roles is not None:
            roles = {r.code for r in model.roles}
        return User(
            id=model.id,
            firebase_uid=model.firebase_uid,
            email=model.email,
            full_name=model.full_name,
            avatar_url=model.avatar_url,
            email_verified=model.email_verified,
            is_active=model.is_active,
            roles=roles,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
