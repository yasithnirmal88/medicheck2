from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    READ_USER = "read:user"
    UPDATE_USER = "update:user"
    DELETE_USER = "delete:user"
    READ_USERS_ALL = "read:users:all"
    MANAGE_ROLES = "manage:roles"
    READ_HEALTH = "read:health"
    READ_ASSESSMENTS = "read:assessments"
    CREATE_ASSESSMENTS = "create:assessments"
    READ_ASSESSMENTS_ALL = "read:assessments:all"
    MANAGE_CONTENT = "manage:content"
    MANAGE_SYSTEM = "manage:system"

    CMS_READ_BODY_SYSTEM = "cms:read:body_system"
    CMS_WRITE_BODY_SYSTEM = "cms:write:body_system"
    CMS_READ_DISEASE = "cms:read:disease"
    CMS_WRITE_DISEASE = "cms:write:disease"
    CMS_READ_INDICATOR = "cms:read:indicator"
    CMS_WRITE_INDICATOR = "cms:write:indicator"
    CMS_READ_SYMPTOM = "cms:read:symptom"
    CMS_WRITE_SYMPTOM = "cms:write:symptom"
    CMS_READ_QUESTION = "cms:read:question"
    CMS_WRITE_QUESTION = "cms:write:question"
    CMS_READ_QUESTION_GROUP = "cms:read:question_group"
    CMS_WRITE_QUESTION_GROUP = "cms:write:question_group"
    CMS_READ_RULE = "cms:read:rule"
    CMS_WRITE_RULE = "cms:write:rule"
    CMS_READ_LAB_TEST = "cms:read:lab_test"
    CMS_WRITE_LAB_TEST = "cms:write:lab_test"
    CMS_READ_IMAGING = "cms:read:imaging"
    CMS_WRITE_IMAGING = "cms:write:imaging"
    CMS_READ_EVIDENCE = "cms:read:evidence"
    CMS_WRITE_EVIDENCE = "cms:write:evidence"
    CMS_READ_RECOMMENDATION = "cms:read:recommendation"
    CMS_WRITE_RECOMMENDATION = "cms:write:recommendation"
    CMS_READ_LIFESTYLE = "cms:read:lifestyle"
    CMS_WRITE_LIFESTYLE = "cms:write:lifestyle"
    CMS_READ_EXERCISE = "cms:read:exercise"
    CMS_WRITE_EXERCISE = "cms:write:exercise"
    CMS_READ_NUTRITION = "cms:read:nutrition"
    CMS_WRITE_NUTRITION = "cms:write:nutrition"
    CMS_READ_TEMPLATE = "cms:read:template"
    CMS_WRITE_TEMPLATE = "cms:write:template"
    CMS_READ_KNOWLEDGE_GRAPH = "cms:read:knowledge_graph"
    CMS_WRITE_KNOWLEDGE_GRAPH = "cms:write:knowledge_graph"
    CMS_READ_AUDIT = "cms:read:audit"
    CMS_READ_VERSION_HISTORY = "cms:read:version_history"
    CMS_WRITE_PUBLISH = "cms:write:publish"
    CMS_APPROVE_CONTENT = "cms:approve:content"
    CMS_READ_DASHBOARD = "cms:read:dashboard"
    CMS_MANAGE_USERS = "cms:manage:users"
    CMS_READ_CLINICAL_GUIDELINE = "cms:read:clinical_guideline"
    CMS_WRITE_CLINICAL_GUIDELINE = "cms:write:clinical_guideline"
    CMS_READ_MEDICATION = "cms:read:medication"
    CMS_WRITE_MEDICATION = "cms:write:medication"
    CMS_READ_APPROVAL = "cms:read:approval"
    CMS_WRITE_APPROVAL = "cms:write:approval"
    CMS_READ_WORKFLOW = "cms:read:workflow"
    CMS_WRITE_WORKFLOW = "cms:write:workflow"
    CMS_READ_SCORING = "cms:read:scoring"
    CMS_WRITE_SCORING = "cms:write:scoring"
    CMS_READ_RISK = "cms:read:risk"
    CMS_WRITE_RISK = "cms:write:risk"
    CMS_READ_SPECIALTY = "cms:read:specialty"
    CMS_WRITE_SPECIALTY = "cms:write:specialty"
    CMS_READ_TAG = "cms:read:tag"
    CMS_WRITE_TAG = "cms:write:tag"
    CMS_READ_CATEGORY = "cms:read:category"
    CMS_WRITE_CATEGORY = "cms:write:category"
    CMS_READ_REFERENCE = "cms:read:reference"
    CMS_WRITE_REFERENCE = "cms:write:reference"
    CMS_READ_ORGANIZATION = "cms:read:organization"
    CMS_WRITE_ORGANIZATION = "cms:write:organization"
    CMS_READ_CHANGE_REQUEST = "cms:read:change_request"
    CMS_WRITE_CHANGE_REQUEST = "cms:write:change_request"
    CMS_READ_NOTIFICATION = "cms:read:notification"
    CMS_WRITE_NOTIFICATION = "cms:write:notification"
    CMS_READ_LIBRARY = "cms:read:library"
    CMS_WRITE_LIBRARY = "cms:write:library"
    # Phase 6 — Population health + SDG analytics. Grants read access to
    # de-identified, aggregated population metrics. Never grants individual
    # patient data access.
    ANALYTICS_VIEW_POPULATION = "analytics:view:population"
    # Phase 7 — AI governance. Grants read access to aggregate AI quality
    # metrics (fallback rate, validation failures, language distribution).
    # Never grants access to patient PHI or individual AI audit records.
    AI_VIEW_GOVERNANCE = "ai:view:governance"


class Role(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    SUPER_ADMIN = "super_admin"
    MEDICAL_DIRECTOR = "medical_director"
    SPECIALIST_DOCTOR = "specialist_doctor"
    GENERAL_PHYSICIAN = "general_physician"
    RESEARCH_REVIEWER = "research_reviewer"
    CONTENT_EDITOR = "content_editor"
    READ_ONLY_REVIEWER = "read_only_reviewer"

    @property
    def permissions(self) -> set[Permission]:
        return _ROLE_PERMISSIONS_MAP.get(self, set())

    @property
    def display_name(self) -> str:
        return _ROLE_DISPLAY_NAMES.get(self, self.value.replace("_", " ").title())


_ROLE_DISPLAY_NAMES: dict[Role, str] = {
    Role.PATIENT: "Patient",
    Role.DOCTOR: "Doctor",
    Role.MEDICAL_DIRECTOR: "Medical Director",
    Role.SPECIALIST_DOCTOR: "Specialist Doctor",
    Role.GENERAL_PHYSICIAN: "General Physician",
    Role.RESEARCH_REVIEWER: "Research Reviewer",
    Role.CONTENT_EDITOR: "Content Editor",
    Role.READ_ONLY_REVIEWER: "Read-Only Reviewer",
    Role.SUPER_ADMIN: "Super Admin",
}


_READ_ALL: set[Permission] = {
    Permission.CMS_READ_BODY_SYSTEM,
    Permission.CMS_READ_DISEASE,
    Permission.CMS_READ_INDICATOR,
    Permission.CMS_READ_SYMPTOM,
    Permission.CMS_READ_QUESTION,
    Permission.CMS_READ_QUESTION_GROUP,
    Permission.CMS_READ_RULE,
    Permission.CMS_READ_LAB_TEST,
    Permission.CMS_READ_IMAGING,
    Permission.CMS_READ_EVIDENCE,
    Permission.CMS_READ_RECOMMENDATION,
    Permission.CMS_READ_LIFESTYLE,
    Permission.CMS_READ_EXERCISE,
    Permission.CMS_READ_NUTRITION,
    Permission.CMS_READ_TEMPLATE,
    Permission.CMS_READ_KNOWLEDGE_GRAPH,
    Permission.CMS_READ_AUDIT,
    Permission.CMS_READ_VERSION_HISTORY,
    Permission.CMS_READ_DASHBOARD,
    Permission.CMS_READ_CLINICAL_GUIDELINE,
    Permission.CMS_READ_MEDICATION,
    Permission.CMS_READ_APPROVAL,
    Permission.CMS_READ_WORKFLOW,
    Permission.CMS_READ_SCORING,
    Permission.CMS_READ_RISK,
    Permission.CMS_READ_SPECIALTY,
    Permission.CMS_READ_TAG,
    Permission.CMS_READ_CATEGORY,
    Permission.CMS_READ_REFERENCE,
    Permission.CMS_READ_ORGANIZATION,
    Permission.CMS_READ_CHANGE_REQUEST,
    Permission.CMS_READ_NOTIFICATION,
    Permission.CMS_READ_LIBRARY,
}

_WRITE_ALL: set[Permission] = {
    Permission.CMS_WRITE_BODY_SYSTEM,
    Permission.CMS_WRITE_DISEASE,
    Permission.CMS_WRITE_INDICATOR,
    Permission.CMS_WRITE_SYMPTOM,
    Permission.CMS_WRITE_QUESTION,
    Permission.CMS_WRITE_QUESTION_GROUP,
    Permission.CMS_WRITE_RULE,
    Permission.CMS_WRITE_LAB_TEST,
    Permission.CMS_WRITE_IMAGING,
    Permission.CMS_WRITE_EVIDENCE,
    Permission.CMS_WRITE_RECOMMENDATION,
    Permission.CMS_WRITE_LIFESTYLE,
    Permission.CMS_WRITE_EXERCISE,
    Permission.CMS_WRITE_NUTRITION,
    Permission.CMS_WRITE_TEMPLATE,
    Permission.CMS_WRITE_KNOWLEDGE_GRAPH,
    Permission.CMS_WRITE_PUBLISH,
    Permission.CMS_APPROVE_CONTENT,
    Permission.CMS_WRITE_CLINICAL_GUIDELINE,
    Permission.CMS_WRITE_MEDICATION,
    Permission.CMS_WRITE_APPROVAL,
    Permission.CMS_WRITE_WORKFLOW,
    Permission.CMS_WRITE_SCORING,
    Permission.CMS_WRITE_RISK,
    Permission.CMS_WRITE_SPECIALTY,
    Permission.CMS_WRITE_TAG,
    Permission.CMS_WRITE_CATEGORY,
    Permission.CMS_WRITE_REFERENCE,
    Permission.CMS_WRITE_ORGANIZATION,
    Permission.CMS_WRITE_CHANGE_REQUEST,
    Permission.CMS_WRITE_NOTIFICATION,
    Permission.CMS_WRITE_LIBRARY,
}


_ROLE_PERMISSIONS_MAP: dict[Role, set[Permission]] = {
    Role.PATIENT: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.READ_ASSESSMENTS,
        Permission.CREATE_ASSESSMENTS,
        Permission.READ_HEALTH,
    },
    Role.DOCTOR: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.READ_ASSESSMENTS,
        Permission.CREATE_ASSESSMENTS,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
    },
    Role.READ_ONLY_REVIEWER: {
        Permission.READ_USER,
        Permission.READ_ASSESSMENTS,
        Permission.CMS_READ_DASHBOARD,
    } | _READ_ALL,
    Role.CONTENT_EDITOR: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.READ_ASSESSMENTS,
        Permission.CREATE_ASSESSMENTS,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_WRITE_QUESTION,
        Permission.CMS_WRITE_QUESTION_GROUP,
        Permission.CMS_WRITE_RULE,
        Permission.CMS_WRITE_BODY_SYSTEM,
        Permission.CMS_WRITE_INDICATOR,
        Permission.CMS_WRITE_SYMPTOM,
        Permission.CMS_WRITE_TEMPLATE,
        Permission.CMS_READ_VERSION_HISTORY,
    } | _READ_ALL,
    Role.GENERAL_PHYSICIAN: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.READ_ASSESSMENTS,
        Permission.CREATE_ASSESSMENTS,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_WRITE_INDICATOR,
        Permission.CMS_WRITE_SYMPTOM,
        Permission.CMS_WRITE_RULE,
        Permission.CMS_WRITE_RECOMMENDATION,
        Permission.CMS_WRITE_LIFESTYLE,
        Permission.CMS_READ_VERSION_HISTORY,
    } | _READ_ALL,
    Role.SPECIALIST_DOCTOR: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_WRITE_DISEASE,
        Permission.CMS_WRITE_INDICATOR,
        Permission.CMS_WRITE_SYMPTOM,
        Permission.CMS_WRITE_RULE,
        Permission.CMS_WRITE_LAB_TEST,
        Permission.CMS_WRITE_IMAGING,
        Permission.CMS_WRITE_EVIDENCE,
        Permission.CMS_WRITE_RECOMMENDATION,
        Permission.CMS_WRITE_LIFESTYLE,
        Permission.CMS_WRITE_EXERCISE,
        Permission.CMS_WRITE_NUTRITION,
        Permission.CMS_WRITE_KNOWLEDGE_GRAPH,
        Permission.CMS_READ_VERSION_HISTORY,
        Permission.CMS_WRITE_PUBLISH,
    } | _READ_ALL,
    Role.RESEARCH_REVIEWER: {
        Permission.READ_USER,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_WRITE_EVIDENCE,
        Permission.CMS_WRITE_KNOWLEDGE_GRAPH,
        Permission.CMS_READ_VERSION_HISTORY,
        Permission.CMS_APPROVE_CONTENT,
        Permission.ANALYTICS_VIEW_POPULATION,
        Permission.AI_VIEW_GOVERNANCE,
    } | _READ_ALL,
    Role.MEDICAL_DIRECTOR: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.READ_USERS_ALL,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_MANAGE_USERS,
        Permission.CMS_READ_VERSION_HISTORY,
        Permission.CMS_APPROVE_CONTENT,
        Permission.CMS_WRITE_PUBLISH,
        Permission.ANALYTICS_VIEW_POPULATION,
        Permission.AI_VIEW_GOVERNANCE,
    } | _READ_ALL | _WRITE_ALL,
    Role.SUPER_ADMIN: {
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.READ_USERS_ALL,
        Permission.MANAGE_ROLES,
        Permission.READ_ASSESSMENTS_ALL,
        Permission.READ_HEALTH,
        Permission.MANAGE_CONTENT,
        Permission.MANAGE_SYSTEM,
        Permission.CMS_READ_DASHBOARD,
        Permission.CMS_MANAGE_USERS,
        Permission.CMS_READ_VERSION_HISTORY,
        Permission.CMS_APPROVE_CONTENT,
        Permission.CMS_WRITE_PUBLISH,
        Permission.ANALYTICS_VIEW_POPULATION,
        Permission.AI_VIEW_GOVERNANCE,
    } | _READ_ALL | _WRITE_ALL,
}

_ROLE_HIERARCHY: dict[Role, int] = {
    Role.PATIENT: 0,
    Role.READ_ONLY_REVIEWER: 5,
    Role.GENERAL_PHYSICIAN: 10,
    Role.DOCTOR: 10,
    Role.CONTENT_EDITOR: 15,
    Role.SPECIALIST_DOCTOR: 20,
    Role.RESEARCH_REVIEWER: 25,
    Role.MEDICAL_DIRECTOR: 30,
    Role.SUPER_ADMIN: 40,
}


def check_permission(
    user_permissions: set[Permission] | set[str],
    required_permission: Permission,
) -> bool:
    return required_permission in user_permissions


def has_role(
    user_roles: set[Role] | set[str],
    required_role: Role,
) -> bool:
    normalized_roles: set[Role] = set()
    for r in user_roles:
        if isinstance(r, Role):
            normalized_roles.add(r)
        else:
            try:
                normalized_roles.add(Role(r))
            except ValueError:
                continue

    required_level = _ROLE_HIERARCHY.get(required_role, 0)
    for role in normalized_roles:
        if _ROLE_HIERARCHY.get(role, 0) >= required_level:
            return True
    return False


def get_role_permissions(role: Role) -> set[Permission]:
    return _ROLE_PERMISSIONS_MAP.get(role, set())


def get_all_permissions() -> set[Permission]:
    all_perms: set[Permission] = set()
    for perms in _ROLE_PERMISSIONS_MAP.values():
        all_perms.update(perms)
    return all_perms


def get_role_hierarchy() -> dict[str, int]:
    return {r.value: _ROLE_HIERARCHY[r] for r in Role}


ROLE_PERMISSIONS_MAP: dict[str, list[str]] = {
    r.value: [p.value for p in _ROLE_PERMISSIONS_MAP.get(r, set())]
    for r in Role
}
