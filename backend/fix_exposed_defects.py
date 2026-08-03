from pathlib import Path

root = Path(r"C:\Users\DELL\Documents\GitHub\medicheck\backend")
repo = root / "app/infrastructure/persistence/repositories/sql_user_repository.py"
text = repo.read_text(encoding="utf-8")
text = text.replace("            is_active=model.is_active,\n            last_login_at=model.last_login_at,", "            is_active=model.is_active,\n            roles=set(),\n            last_login_at=model.last_login_at,")
repo.write_text(text, encoding="utf-8")

profile = root / "app/infrastructure/persistence/repositories/sql_profile_repository.py"
text = profile.read_text(encoding="utf-8")
text = text.replace("from sqlalchemy import insert, select, update", "from sqlalchemy import insert, select, update\nfrom sqlalchemy.orm import selectinload")
text = text.replace(
    "q = select(HealthProfileModel).where(HealthProfileModel.user_id == user_id)",
    "q = (select(HealthProfileModel).options(selectinload(HealthProfileModel.personal_info), selectinload(HealthProfileModel.lifestyle), selectinload(HealthProfileModel.nutrition)).where(HealthProfileModel.user_id == user_id))"
)
text = text.replace(
    "q = select(HealthProfileModel).where(HealthProfileModel.id == profile_id)",
    "q = (select(HealthProfileModel).options(selectinload(HealthProfileModel.personal_info), selectinload(HealthProfileModel.lifestyle), selectinload(HealthProfileModel.nutrition)).where(HealthProfileModel.id == profile_id))"
)
profile.write_text(text, encoding="utf-8")

for name in ["test_admin_service.py", "test_clinical_decision_service.py", "test_knowledge_graph.py", "test_report_service.py"]:
    p = root / "tests" / name
    t = p.read_text(encoding="utf-8")
    if "BodySystemModel" not in t:
        insert_at = t.find("\n\n", t.find("from app."))
        t = t[:insert_at] + "\nfrom app.infrastructure.persistence.models.body_system import BodySystemModel" + t[insert_at:]
    marker = "    session = db_session\n"
    setup = "    await session.execute(BodySystemModel.__table__.insert().values(id=\"body-system-1\", code=\"test-system\", name=\"Test System\"))\n    await session.commit()\n"
    t = t.replace(marker, marker + setup)
    t = t.replace('"body_system_id": None,', '"body_system_id": "body-system-1",')
    t = t.replace('.values(key="i1", name="Ind 1")', '.values(key="i1", name="Ind 1", body_system_id="body-system-1")')
    t = t.replace('"unit": "mmol/L",', '"unit": "mmol/L",\n            "body_system_id": "body-system-1",')
    t = t.replace('key="ind-1", name="Indicator 1"', 'key="ind-1", name="Indicator 1", body_system_id="body-system-1"')
    p.write_text(t, encoding="utf-8")
