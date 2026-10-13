"""Identity boundary enforcement.

Application code OUTSIDE the identity-owned files must consume identity
concerns ONLY through the ``app.identity`` public interface — never by
importing identity internals directly. This test AST-scans ``app/`` and fails
on any direct internal import from a non-identity module.

Identity-owned files (may use internals): the implementations themselves,
the identity HTTP API (auth/users/identity_admin endpoints), the composition
root, and the facade. Tests are exempt (they may probe internals such as mock
helpers and private RBAC maps). No exemptions remain: former SQL-level
``UserModel`` joins now go through ``app.identity.queries``.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT / "app"


def _p(*parts: str) -> str:
    return str(Path(*parts).as_posix())


IDENTITY_OWNED = {
    _p("app", "identity", "__init__.py"),
    _p("app", "identity", "permissions.py"),
    _p("app", "identity", "queries.py"),
    _p("app", "core", "security", "firebase.py"),
    _p("app", "core", "security", "rbac.py"),
    _p("app", "domain", "entities", "user.py"),
    _p("app", "domain", "repositories", "user_repository.py"),
    _p("app", "application", "services", "auth_service.py"),
    _p("app", "application", "dtos", "auth_dtos.py"),
    _p("app", "infrastructure", "persistence", "models", "user.py"),
    _p("app", "infrastructure", "persistence", "models", "role.py"),
    _p("app", "infrastructure", "persistence", "models", "user_role.py"),
    _p(
        "app",
        "infrastructure",
        "persistence",
        "repositories",
        "sql_user_repository.py",
    ),
    _p("app", "api", "deps.py"),
    _p("app", "api", "v1", "endpoints", "auth.py"),
    _p("app", "api", "v1", "endpoints", "users.py"),
    _p("app", "api", "v1", "endpoints", "identity_admin.py"),
    _p("app", "main.py"),
}

#: Internal identity modules that non-identity app code must not import.
DENIED_MODULES = {
    "app.core.security.firebase",
    "app.core.security.rbac",
    "app.domain.entities.user",
    "app.domain.entities.role",
    "app.domain.repositories.user_repository",
    "app.application.services.auth_service",
    "app.application.dtos.auth_dtos",
    "app.infrastructure.persistence.models.user",
    "app.infrastructure.persistence.models.role",
    "app.infrastructure.persistence.models.user_role",
    "app.infrastructure.persistence.repositories.sql_user_repository",
    "app.infrastructure.auth.firebase_provider",
}

#: Identity dep names in app.api.deps — import these from app.identity instead.
#: get_db/get_redis stay in app.api.deps (not identity concerns).
IDENTITY_DEP_NAMES = {
    "get_current_user",
    "get_current_active_user",
    "get_current_doctor",
    "get_current_admin",
    "get_current_super_admin",
    "get_cms_user",
    "get_analytics_user",
    "get_ai_governance_user",
    "get_chw_user",
    "get_interop_user",
    "get_referral_user",
    "get_sdg_export_user",
}

#: Formerly-grandfathered per-file exemptions. All resolved: SQL-level
#: UserModel joins moved behind app.identity.queries and the CMS
#: permission-SQL copies were replaced by app.identity.get_user_permissions.
#: The dict stays (empty) so a future exemption, if ever needed, is explicit
#: and reviewable — but the goal is to keep it empty.
GRANDFATHERED: dict[str, set[str]] = {}


def _violations_in(path: Path) -> list[str]:
    rel = path.relative_to(BACKEND_ROOT).as_posix()
    if rel in IDENTITY_OWNED:
        return []
    allowed = GRANDFATHERED.get(rel, set())
    try:
        tree = ast.parse(path.read_bytes(), filename=str(path))
    except SyntaxError as exc:
        return [f"{rel}: unparsable ({exc})"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in DENIED_MODULES and module not in allowed:
                violations.append(f"{rel}:{node.lineno} imports internal {module}")
            elif module == "app.api.deps":
                bad = sorted(
                    a.name for a in node.names if a.name in IDENTITY_DEP_NAMES
                )
                if bad:
                    violations.append(
                        f"{rel}:{node.lineno} imports identity dep(s) {bad} "
                        "from app.api.deps — use app.identity"
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DENIED_MODULES and alias.name not in allowed:
                    violations.append(
                        f"{rel}:{node.lineno} imports internal {alias.name}"
                    )
                elif alias.name == "app.api.deps":
                    violations.append(
                        f"{rel}:{node.lineno} imports app.api.deps bare — "
                        "import get_db/get_redis from app.api.deps and "
                        "identity deps from app.identity"
                    )
    return violations


def test_identity_boundary():
    violations: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        violations.extend(_violations_in(path))
    assert not violations, (
        "Identity boundary violations (import via app.identity instead):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_facade_exports_public_interface():
    import app.identity as ident

    for name in (
        "User",
        "Role",
        "Permission",
        "AuthService",
        "UserRepository",
        "has_role",
        "check_permission",
        "get_role_permissions",
        "get_user_permissions",
        "verify_firebase_token",
        "mock_email_for_uid",
        "get_current_user",
        "get_current_active_user",
        "get_cms_user",
        "get_ai_governance_user",
        "get_chw_user",
        "get_referral_user",
        "UserResponse",
        "AuthenticatedUserResponse",
    ):
        assert hasattr(ident, name), f"app.identity must export {name}"
    assert set(ident.__all__) >= {
        "User",
        "Role",
        "Permission",
        "AuthService",
        "has_role",
        "get_current_user",
    }
