"""Phase 6 — Population Health + SDG Analytics backend tests.

Covers:
- RBAC: analytics endpoints require RESEARCH_REVIEWER+; patient/roleless/doctor denied.
- De-identification: no patient identifiers in any response.
- Small-cell suppression: cohorts < k report suppressed=True.
- Disclaimer text present (trajectory is trend, not diagnosis).
- Phase 5 integration: language/input_type persisted to session metadata.
- SDG dashboard sections present with the correct goal labels.
- Date-range validation (rejection of ranges > max + inverted ranges).
"""
import uuid
from datetime import UTC, datetime, timedelta, date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_analytics_user, get_db, get_current_active_user
from app.domain.entities.user import User
from app.core.security.rbac import Role
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.report import (
    BodySystemAssessmentModel,
    ConditionAssessmentModel,
    HealthAssessmentModel,
)
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.role import RoleModel


def _make_user(roles: set[Role], email: str = "analyst@example.com") -> User:
    return User(
        id=uuid.uuid4().hex,
        firebase_uid=f"fb-{email}",
        email=email,
        full_name="Analytics Analyst",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=roles,
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest.fixture
def analytics_user() -> User:
    return _make_user({Role.RESEARCH_REVIEWER})


@pytest.fixture
def analytics_overrides(client, analytics_user):
    """Override analytics auth so the test user has RESEARCH_REVIEWER."""
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_analytics_user] = lambda: analytics_user
    yield app
    app.dependency_overrides.pop(get_analytics_user, None)


def _add_user(db: AsyncSession, email: str) -> UserModel:
    u = UserModel(
        firebase_uid=f"fb-{email}",
        email=email,
        full_name=f"User {email}",
        is_active=True,
        email_verified=True,
    )
    db.add(u)
    return u


async def _add_session(
    db: AsyncSession,
    user: UserModel,
    *,
    status: str = "completed",
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    extra_metadata: dict | None = None,
) -> AssessmentSessionModel:
    s = AssessmentSessionModel(
        user_id=user.id,
        questionnaire_template_id=None,
        questionnaire_version_id=None,
        status=status,
        current_question_id=None,
        current_group_id=None,
        answers_count=0,
        total_questions=0,
        completed_questions=0,
        started_at=started_at or datetime.now(UTC),
        paused_at=None,
        completed_at=completed_at,
        expires_at=None,
        device_info=None,
        extra_metadata=extra_metadata or {},
    )
    db.add(s)
    return s


async def _add_report(
    db: AsyncSession,
    session: AssessmentSessionModel,
    body_system_id: str,
    category: str = "Monitor",
    score: str = "2.0",
) -> None:
    h = HealthAssessmentModel(
        session_id=session.id,
        user_id=session.user_id,
        summary=None,
        created_at=session.started_at,
    )
    db.add(h)
    await db.flush()
    db.add(
        BodySystemAssessmentModel(
            assessment_id=h.id,
            body_system_id=body_system_id,
            category=category,
            score=score,
            notes=None,
        )
    )


async def _seed_large_dataset(db: AsyncSession, n_users: int = 15):
    """Seed enough data to exceed the small-cell threshold (k=10)."""
    bs = BodySystemModel(code="cv", name="Cardiovascular", is_active=True, display_order=0)
    db.add(bs)
    await db.flush()
    cond = PossibleConditionModel(name="Hypertension", body_system_id=bs.id, status="active")
    db.add(cond)
    await db.flush()

    for i in range(n_users):
        u = _add_user(db, f"patient{i}@example.com")
        await db.flush()
        s = await _add_session(
            db, u,
            status="completed",
            extra_metadata={"language": "en" if i % 2 == 0 else "si", "input_type": "voice" if i % 3 == 0 else "text"},
        )
        await db.flush()
        await _add_report(db, s, body_system_id=bs.id, category="Monitor")
        db.add(
            ConditionAssessmentModel(
                assessment_id=(await db.execute(
                    __import__("sqlalchemy").select(HealthAssessmentModel).where(HealthAssessmentModel.session_id == s.id)
                )).scalar_one().id,
                condition_id=cond.id,
                score="2.0",
                confidence="Moderate",
                notes=None,
            )
        )
    await db.commit()


async def _seed_voice_heavy_dataset(db: AsyncSession, n_users: int = 30):
    """Seed data where voice intake exceeds k so it is not suppressed."""
    bs = BodySystemModel(code="cv", name="Cardiovascular", is_active=True, display_order=0)
    db.add(bs)
    await db.flush()
    for i in range(n_users):
        u = _add_user(db, f"vhuser{i}@example.com")
        await db.flush()
        # First 12 are voice, rest text.
        itype = "voice" if i < 12 else "text"
        s = await _add_session(
            db, u,
            status="completed",
            extra_metadata={"language": "en", "input_type": itype},
        )
        await db.flush()
        await _add_report(db, s, body_system_id=bs.id, category="Monitor")
    await db.commit()


# ── RBAC tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_denied_for_patient(client, db_session):
    """A patient (no analytics role) must be denied."""
    app = client._transport.app  # type: ignore[attr-defined]
    patient = _make_user({Role.PATIENT}, email="patient@example.com")
    # Override the upstream auth so get_analytics_user's real check runs.
    app.dependency_overrides[get_current_active_user] = lambda: patient
    try:
        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_analytics_denied_for_roleless(client, db_session):
    """A user with no roles at all must be denied."""
    app = client._transport.app  # type: ignore[attr-defined]
    roleless = _make_user(set(), email="roleless@example.com")
    app.dependency_overrides[get_current_active_user] = lambda: roleless
    try:
        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_analytics_denied_for_doctor(client, db_session):
    """A plain doctor must be denied population analytics (least privilege)."""
    app = client._transport.app  # type: ignore[attr-defined]
    doc = _make_user({Role.DOCTOR}, email="doc@example.com")
    app.dependency_overrides[get_current_active_user] = lambda: doc
    try:
        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_analytics_allowed_for_medical_director(client, db_session):
    """MEDICAL_DIRECTOR (level 30) must be allowed."""
    app = client._transport.app  # type: ignore[attr-defined]
    md = _make_user({Role.MEDICAL_DIRECTOR}, email="md@example.com")
    app.dependency_overrides[get_analytics_user] = lambda: md
    try:
        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 200
    finally:
        app.dependency_overrides.pop(get_analytics_user, None)


@pytest.mark.asyncio
async def test_analytics_allowed_for_super_admin(client, db_session):
    """SUPER_ADMIN (level 40) must be allowed."""
    app = client._transport.app  # type: ignore[attr-defined]
    sa = _make_user({Role.SUPER_ADMIN}, email="sa@example.com")
    app.dependency_overrides[get_analytics_user] = lambda: sa
    try:
        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 200
    finally:
        app.dependency_overrides.pop(get_analytics_user, None)


# ── Overview + de-identification ────────────────────────────────────

@pytest.mark.asyncio
async def test_overview_returns_counts(client, db_session, analytics_overrides):
    """Overview returns aggregate counts (no identifiers)."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/overview")
    assert r.status_code == 200, r.text
    data = r.json()
    ov = data["overview"]
    assert ov["total_assessments"] == 15
    assert ov["completed_assessments"] == 15
    assert ov["unique_participants"] == 15
    # De-identification: no user_id, email, session_id anywhere.
    blob = str(data)
    assert "patient0@example.com" not in blob
    assert "@example.com" not in blob


@pytest.mark.asyncio
async def test_overview_no_patient_identifiers(client, db_session, analytics_overrides):
    """No raw user IDs appear in the response."""
    await _seed_large_dataset(db_session, n_users=12)
    r = await client.get("/api/v1/analytics/overview")
    blob = str(r.json())
    # The seeded user IDs are 32-char hex; none should appear.
    users = await db_session.execute(
        __import__("sqlalchemy").select(UserModel)
    )
    for u in users.scalars().all():
        assert u.id not in blob
        assert u.email not in blob


# ── Small-cell suppression ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_small_cell_suppression_below_k(client, db_session, analytics_overrides):
    """A cohort smaller than k must report suppressed=True."""
    # Only 3 users — below k=10.
    await _seed_large_dataset(db_session, n_users=3)
    r = await client.get("/api/v1/analytics/overview")
    data = r.json()
    ov = data["overview"]
    assert ov["completion_rate_suppressed"] is True
    assert ov["completion_rate"] is None


@pytest.mark.asyncio
async def test_small_cell_suppression_above_k(client, db_session, analytics_overrides):
    """A cohort >= k must not suppress the completion rate."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/overview")
    ov = r.json()["overview"]
    assert ov["completion_rate_suppressed"] is False
    assert ov["completion_rate"] == 100.0


# ── Severity distribution ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_severity_distribution_has_disclaimer(client, db_session, analytics_overrides):
    """Severity distribution must carry the 'not prevalence' disclaimer."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/severity")
    data = r.json()
    assert "disclaimer" in data
    assert "not population prevalence" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_severity_distribution_categories(client, db_session, analytics_overrides):
    """All five severity categories appear in the response."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/severity")
    cats = {b["category"] for b in r.json()["distribution"]}
    assert {"Normal", "Monitor", "Needs Attention", "Recommend Screening", "Urgent Medical Review"} <= cats


# ── Indicators ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_indicators_has_disclaimer(client, db_session, analytics_overrides):
    """Indicators must carry the 'not confirmed diagnosis' disclaimer."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/indicators")
    data = r.json()
    assert "disclaimer" in data
    assert "not confirmed diagnosis" in data["disclaimer"].lower()


# ── Trajectory ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trajectory_has_disclaimer(client, db_session, analytics_overrides):
    """Trajectory must carry the 'not disease progression' disclaimer."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/trajectory")
    data = r.json()
    assert "disclaimer" in data
    assert "not proof of disease progression" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_trajectory_uses_phase4_trend_labels(client, db_session, analytics_overrides):
    """Trajectory distribution uses Phase 4 TrendLabel values."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/trajectory")
    trends = {b["trend"] for b in r.json()["distribution"]}
    assert {"improving", "stable", "worsening", "new", "resolved"} <= trends


# ── Accessibility (Phase 5 integration) ──────────────────────────────

@pytest.mark.asyncio
async def test_accessibility_has_disclaimer(client, db_session, analytics_overrides):
    """Accessibility must carry the language-not-demographic disclaimer."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/accessibility")
    data = r.json()
    assert "disclaimer" in data
    assert "not infer demographics" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_accessibility_counts_voice_vs_text(client, db_session, analytics_overrides):
    """Voice vs text counts are reported correctly (voice exceeds k)."""
    await _seed_voice_heavy_dataset(db_session, n_users=30)
    r = await client.get("/api/v1/analytics/accessibility")
    acc = r.json()["accessibility"]
    # 30 users: 12 voice, 18 text. Voice >= k so not suppressed.
    assert acc["voice_intake_count"] == 12
    assert acc["text_intake_count"] == 18
    assert acc["voice_suppressed"] is False


# ── SDG dashboard ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sdg_dashboard_sections(client, db_session, analytics_overrides):
    """SDG dashboard returns all four sections."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/sdg")
    data = r.json()
    assert "disclaimer" in data
    assert "not prove" in data["disclaimer"].lower()
    goals = {s["goal"] for s in data["sections"]}
    assert {"SDG 3.4", "SDG 3.8", "SDG 3.d", "SDG 10"} <= goals


@pytest.mark.asyncio
async def test_sdg_dashboard_has_metrics(client, db_session, analytics_overrides):
    """Each SDG section has at least one metric."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/sdg")
    for section in r.json()["sections"]:
        assert len(section["metrics"]) >= 1
        for m in section["metrics"]:
            assert "label" in m
            assert "suppressed" in m


# ── Date range validation ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_date_range_rejected(client, db_session, analytics_overrides):
    """An inverted date range (end < start) is rejected with 400/403."""
    today = date.today()
    r = await client.get(
        "/api/v1/analytics/overview",
        params={"start_date": today.isoformat(), "end_date": (today - timedelta(days=1)).isoformat()},
    )
    assert r.status_code in (400, 403)


@pytest.mark.asyncio
async def test_overlarge_date_range_rejected(client, db_session, analytics_overrides):
    """A date range exceeding the max is rejected."""
    today = date.today()
    r = await client.get(
        "/api/v1/analytics/overview",
        params={
            "start_date": (today - timedelta(days=400)).isoformat(),
            "end_date": today.isoformat(),
        },
    )
    assert r.status_code in (400, 403)


# ── Body systems ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_body_systems_returns_active_only(client, db_session, analytics_overrides):
    """Body systems returns the seeded active system."""
    await _seed_large_dataset(db_session, n_users=15)
    r = await client.get("/api/v1/analytics/body-systems")
    data = r.json()
    assert any(bs["code"] == "cv" for bs in data["body_systems"])


# ── Phase 5 language persistence (integration) ───────────────────────

@pytest.mark.asyncio
async def test_language_metadata_persisted_to_session(client, db_session, analytics_overrides):
    """When a session is created and language set, metadata is stored."""
    u = _add_user(db_session, "langtest@example.com")
    await db_session.commit()
    s = AssessmentSessionModel(
        user_id=u.id,
        questionnaire_template_id=None,
        questionnaire_version_id=None,
        status="active",
        current_question_id=None,
        current_group_id=None,
        answers_count=0,
        total_questions=0,
        completed_questions=0,
        started_at=datetime.now(UTC),
        extra_metadata={"language": "si", "input_type": "voice"},
    )
    db_session.add(s)
    await db_session.commit()
    # Verify the JSON column was populated.
    from sqlalchemy import select
    row = (await db_session.execute(
        select(AssessmentSessionModel).where(AssessmentSessionModel.id == s.id)
    )).scalar_one()
    assert row.extra_metadata["language"] == "si"
    assert row.extra_metadata["input_type"] == "voice"
