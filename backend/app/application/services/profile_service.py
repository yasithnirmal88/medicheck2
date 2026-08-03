from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.profile_dtos import HealthProfileDTO, PersonalInfoDTO
from app.domain.entities.user import User
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SQLProfileRepository(session)

    async def get_or_create_profile_for_user(self, user: User) -> HealthProfileDTO:
        profile = await self.repo.get_by_user_id(user.id)
        if profile is None:
            profile = await self.repo.create_for_user(user.id)
        return HealthProfileDTO.from_orm(profile)

    async def update_personal_info(
        self, user: User, data: PersonalInfoDTO
    ) -> HealthProfileDTO:
        profile = await self.repo.get_or_create_for_user(user.id)
        await self.repo.upsert_personal_info(profile.id, data.dict())
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        updated = await self.repo.get_by_id(profile.id)
        return HealthProfileDTO.from_orm(updated)

    # Lifestyle & Nutrition
    async def update_lifestyle(self, user: User, data: dict) -> HealthProfileDTO:
        profile = await self.repo.get_or_create_for_user(user.id)
        await self.repo.upsert_lifestyle(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        updated = await self.repo.get_by_id(profile.id)
        return HealthProfileDTO.from_orm(updated)

    async def update_nutrition(self, user: User, data: dict) -> HealthProfileDTO:
        profile = await self.repo.get_or_create_for_user(user.id)
        await self.repo.upsert_nutrition(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        updated = await self.repo.get_by_id(profile.id)
        return HealthProfileDTO.from_orm(updated)

    # Repeatable sections add/list
    async def add_medical_history(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_medical_history(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_medical_history(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_medical_history(profile.id)

    async def add_medication(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_medication(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_medications(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_medications(profile.id)

    async def add_surgery(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_surgery(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_surgeries(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_surgeries(profile.id)

    async def add_family_history(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_family_history(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_family_histories(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_family_histories(profile.id)

    async def add_allergy(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_allergy(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_allergies(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_allergies(profile.id)

    async def add_immunization(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_immunization(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_immunizations(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_immunizations(profile.id)

    async def add_measurement(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_measurement(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_measurements(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_measurements(profile.id)

    async def add_lab_report(self, user: User, data: dict):
        profile = await self.repo.get_or_create_for_user(user.id)
        item = await self.repo.add_lab_report(profile.id, data)
        snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, snapshot, created_by=user.id)
        return item

    async def list_lab_reports(self, user: User):
        profile = await self.repo.get_or_create_for_user(user.id)
        return await self.repo.list_lab_reports(profile.id)

    async def get_profile(self, user: User) -> HealthProfileDTO:
        profile = await self.repo.get_or_create_for_user(user.id)
        return HealthProfileDTO.from_orm(profile)

    # Completion calculation
    async def compute_completion(self, user: User) -> dict:
        profile = await self.repo.get_or_create_for_user(user.id)
        # define sections and checks
        sections = {
            "personal_info": bool(getattr(profile, "personal_info", None)),
            "lifestyle": bool(getattr(profile, "lifestyle", None)),
            "nutrition": bool(getattr(profile, "nutrition", None)),
            "medical_history": len(getattr(profile, "medical_histories", [])) > 0,
            "medications": len(getattr(profile, "medication_histories", [])) > 0,
            "surgeries": len(getattr(profile, "surgical_histories", [])) > 0,
            "family_history": len(getattr(profile, "family_histories", [])) > 0,
            "allergies": len(getattr(profile, "allergies", [])) > 0,
            "immunizations": len(getattr(profile, "immunizations", [])) > 0,
            "measurements": len(getattr(profile, "measurements", [])) > 0,
            "lab_reports": len(getattr(profile, "lab_reports", [])) > 0,
        }
        total = len(sections)
        completed = sum(1 for v in sections.values() if v)
        percent = int((completed / total) * 100) if total else 0
        return {
            "overall": percent,
            "completed": completed,
            "total": total,
            "sections": sections,
        }

    # Versioning preview & restore
    async def get_version_snapshot(self, user: User, version: int) -> dict | None:
        profile = await self.repo.get_or_create_for_user(user.id)
        versions = await self.repo.list_versions(profile.id)
        for v in versions:
            if v.version == version:
                return v.snapshot
        return None

    async def restore_version(self, user: User, version: int) -> HealthProfileDTO:
        snapshot = await self.get_version_snapshot(user, version)
        if snapshot is None:
            raise ValueError("version not found")
        profile = await self.repo.get_or_create_for_user(user.id)
        # naive restore: overwrite key sections that exist in snapshot
        # restore personal_info
        if snapshot.get("personal_info"):
            await self.repo.upsert_personal_info(profile.id, snapshot["personal_info"])
        if snapshot.get("lifestyle"):
            await self.repo.upsert_lifestyle(profile.id, snapshot["lifestyle"])
        if snapshot.get("nutrition"):
            await self.repo.upsert_nutrition(profile.id, snapshot["nutrition"])
        # Note: restoring list-based sections (medical_histories etc) requires more sophisticated merging. For now, create new records from snapshot lists if present.
        for key, add_fn in (
            ("medical_history", self.repo.add_medical_history),
            ("medical_histories", self.repo.add_medical_history),
            ("medication", self.repo.add_medication),
            ("medication_histories", self.repo.add_medication),
            ("surgical_histories", self.repo.add_surgery),
            ("family_histories", self.repo.add_family_history),
            ("allergies", self.repo.add_allergy),
            ("immunizations", self.repo.add_immunization),
            ("measurements", self.repo.add_measurement),
            ("lab_reports", self.repo.add_lab_report),
        ):
            items = snapshot.get(key)
            if items and isinstance(items, list):
                for it in items:
                    try:
                        await add_fn(profile.id, it)
                    except Exception:
                        logger.warning("Skipping item %s for profile %s", key, profile.id, exc_info=True)
        # create a new version for the restoration event
        new_snapshot = await self.repo.snapshot_profile(profile.id)
        await self.repo.create_version(profile.id, new_snapshot, created_by=user.id)
        updated = await self.repo.get_by_id(profile.id)
        return HealthProfileDTO.from_orm(updated)
