from __future__ import annotations

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.persistence.models.allergy import AllergyModel
from app.infrastructure.persistence.models.family_history import FamilyHistoryModel
from app.infrastructure.persistence.models.health_profile import HealthProfileModel
from app.infrastructure.persistence.models.immunization import ImmunizationModel
from app.infrastructure.persistence.models.lab_report import LabReportModel
from app.infrastructure.persistence.models.lifestyle import LifestyleModel
from app.infrastructure.persistence.models.measurement import MeasurementModel
from app.infrastructure.persistence.models.medical_history import MedicalHistoryModel
from app.infrastructure.persistence.models.medication_history import (
    MedicationHistoryModel,
)
from app.infrastructure.persistence.models.nutrition import NutritionModel
from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.models.profile_version import ProfileVersionModel
from app.infrastructure.persistence.models.surgical_history import SurgicalHistoryModel


class SQLProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> HealthProfileModel | None:
        q = (
            select(HealthProfileModel)
            .where(HealthProfileModel.user_id == user_id)
            .options(
                selectinload(HealthProfileModel.personal_info),
                selectinload(HealthProfileModel.lifestyle),
                selectinload(HealthProfileModel.nutrition),
            )
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def get_by_id(self, profile_id: str) -> HealthProfileModel | None:
        q = (
            select(HealthProfileModel)
            .where(HealthProfileModel.id == profile_id)
            .options(
                selectinload(HealthProfileModel.personal_info),
                selectinload(HealthProfileModel.lifestyle),
                selectinload(HealthProfileModel.nutrition),
            )
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def create_for_user(self, user_id: str) -> HealthProfileModel:
        stmt = insert(HealthProfileModel).values(user_id=user_id, draft=1)
        await self.session.execute(stmt)
        return await self.get_by_user_id(user_id)

    async def get_or_create_for_user(self, user_id: str) -> HealthProfileModel:
        p = await self.get_by_user_id(user_id)
        if p:
            return p
        return await self.create_for_user(user_id)

    async def upsert_personal_info(self, profile_id: str, data: dict) -> None:
        q = select(PersonalInfoModel).where(PersonalInfoModel.profile_id == profile_id)
        r = await self.session.execute(q)
        row = r.scalars().first()
        if row:
            upd = (
                update(PersonalInfoModel)
                .where(PersonalInfoModel.profile_id == profile_id)
                .values(**data)
            )
            await self.session.execute(upd)
            return
        ins = insert(PersonalInfoModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)

    async def upsert_lifestyle(self, profile_id: str, data: dict) -> None:
        q = select(LifestyleModel).where(LifestyleModel.profile_id == profile_id)
        r = await self.session.execute(q)
        row = r.scalars().first()
        if row:
            upd = (
                update(LifestyleModel)
                .where(LifestyleModel.profile_id == profile_id)
                .values(**data)
            )
            await self.session.execute(upd)
            return
        ins = insert(LifestyleModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)

    async def upsert_nutrition(self, profile_id: str, data: dict) -> None:
        q = select(NutritionModel).where(NutritionModel.profile_id == profile_id)
        r = await self.session.execute(q)
        row = r.scalars().first()
        if row:
            upd = (
                update(NutritionModel)
                .where(NutritionModel.profile_id == profile_id)
                .values(**data)
            )
            await self.session.execute(upd)
            return
        ins = insert(NutritionModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)

    # CRUD for repeatable sections
    async def add_medical_history(
        self, profile_id: str, data: dict
    ) -> MedicalHistoryModel:
        ins = insert(MedicalHistoryModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        # return latest
        q = (
            select(MedicalHistoryModel)
            .where(MedicalHistoryModel.profile_id == profile_id)
            .order_by(MedicalHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_medical_history(self, profile_id: str) -> list[MedicalHistoryModel]:
        q = (
            select(MedicalHistoryModel)
            .where(MedicalHistoryModel.profile_id == profile_id)
            .order_by(MedicalHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_medication(
        self, profile_id: str, data: dict
    ) -> MedicationHistoryModel:
        ins = insert(MedicationHistoryModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(MedicationHistoryModel)
            .where(MedicationHistoryModel.profile_id == profile_id)
            .order_by(MedicationHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_medications(self, profile_id: str) -> list[MedicationHistoryModel]:
        q = (
            select(MedicationHistoryModel)
            .where(MedicationHistoryModel.profile_id == profile_id)
            .order_by(MedicationHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_surgery(self, profile_id: str, data: dict) -> SurgicalHistoryModel:
        ins = insert(SurgicalHistoryModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(SurgicalHistoryModel)
            .where(SurgicalHistoryModel.profile_id == profile_id)
            .order_by(SurgicalHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_surgeries(self, profile_id: str) -> list[SurgicalHistoryModel]:
        q = (
            select(SurgicalHistoryModel)
            .where(SurgicalHistoryModel.profile_id == profile_id)
            .order_by(SurgicalHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_family_history(
        self, profile_id: str, data: dict
    ) -> FamilyHistoryModel:
        ins = insert(FamilyHistoryModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(FamilyHistoryModel)
            .where(FamilyHistoryModel.profile_id == profile_id)
            .order_by(FamilyHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_family_histories(self, profile_id: str) -> list[FamilyHistoryModel]:
        q = (
            select(FamilyHistoryModel)
            .where(FamilyHistoryModel.profile_id == profile_id)
            .order_by(FamilyHistoryModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_allergy(self, profile_id: str, data: dict) -> AllergyModel:
        ins = insert(AllergyModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(AllergyModel)
            .where(AllergyModel.profile_id == profile_id)
            .order_by(AllergyModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_allergies(self, profile_id: str) -> list[AllergyModel]:
        q = (
            select(AllergyModel)
            .where(AllergyModel.profile_id == profile_id)
            .order_by(AllergyModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_immunization(self, profile_id: str, data: dict) -> ImmunizationModel:
        ins = insert(ImmunizationModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(ImmunizationModel)
            .where(ImmunizationModel.profile_id == profile_id)
            .order_by(ImmunizationModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_immunizations(self, profile_id: str) -> list[ImmunizationModel]:
        q = (
            select(ImmunizationModel)
            .where(ImmunizationModel.profile_id == profile_id)
            .order_by(ImmunizationModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_measurement(self, profile_id: str, data: dict) -> MeasurementModel:
        ins = insert(MeasurementModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(MeasurementModel)
            .where(MeasurementModel.profile_id == profile_id)
            .order_by(MeasurementModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_measurements(self, profile_id: str) -> list[MeasurementModel]:
        q = (
            select(MeasurementModel)
            .where(MeasurementModel.profile_id == profile_id)
            .order_by(MeasurementModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def add_lab_report(self, profile_id: str, data: dict) -> LabReportModel:
        ins = insert(LabReportModel).values(profile_id=profile_id, **data)
        await self.session.execute(ins)
        q = (
            select(LabReportModel)
            .where(LabReportModel.profile_id == profile_id)
            .order_by(LabReportModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_lab_reports(self, profile_id: str) -> list[LabReportModel]:
        q = (
            select(LabReportModel)
            .where(LabReportModel.profile_id == profile_id)
            .order_by(LabReportModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def snapshot_profile(self, profile_id: str) -> dict:
        q = (
            select(HealthProfileModel)
            .where(HealthProfileModel.id == profile_id)
            .options(
                selectinload(HealthProfileModel.personal_info),
                selectinload(HealthProfileModel.lifestyle),
                selectinload(HealthProfileModel.nutrition),
            )
        )
        r = await self.session.execute(q)
        profile = r.scalars().first()
        # construct snapshot - lightweight: include profile metadata and personal_info/lifestyle/nutrition
        snapshot = {
            "profile": {
                "id": profile.id,
                "user_id": profile.user_id,
                "draft": bool(profile.draft),
                "metadata": profile.profile_metadata,
            }
        }
        # personal info
        if getattr(profile, "personal_info", None):
            snapshot["personal_info"] = profile.personal_info.to_dict()
        if getattr(profile, "lifestyle", None):
            snapshot["lifestyle"] = profile.lifestyle.to_dict()
        if getattr(profile, "nutrition", None):
            snapshot["nutrition"] = profile.nutrition.to_dict()
        return snapshot

    async def create_version(
        self, profile_id: str, snapshot: dict, created_by: str | None = None
    ) -> ProfileVersionModel:
        # compute next version number
        q = (
            select(ProfileVersionModel)
            .where(ProfileVersionModel.profile_id == profile_id)
            .order_by(ProfileVersionModel.version.desc())
        )
        r = await self.session.execute(q)
        latest = r.scalars().first()
        next_version = 1 if latest is None else latest.version + 1
        ins = insert(ProfileVersionModel).values(
            profile_id=profile_id,
            version=next_version,
            snapshot=snapshot,
            created_by=created_by,
        )
        await self.session.execute(ins)
        # return created
        q2 = (
            select(ProfileVersionModel)
            .where(ProfileVersionModel.profile_id == profile_id)
            .order_by(ProfileVersionModel.version.desc())
        )
        r2 = await self.session.execute(q2)
        return r2.scalars().first()

    async def list_versions(self, profile_id: str) -> list[ProfileVersionModel]:
        q = (
            select(ProfileVersionModel)
            .where(ProfileVersionModel.profile_id == profile_id)
            .order_by(ProfileVersionModel.version.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()
