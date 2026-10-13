"""Identity / Auth bounded context — public interface.

This package is the SINGLE entry point through which the rest of the
application may consume identity concerns (user identity, Firebase token
validation, roles/RBAC, auth dependencies). It is a thin facade: the
implementations stay in their DDD layers (``core/security``,
``domain/entities``, ``application/services``, ``infrastructure``,
``api/deps``); this module only re-exports what other bounded contexts are
allowed to depend on.

Boundary rule: application code OUTSIDE the identity-owned files must import
identity names ONLY from ``app.identity`` (or ``app.identity.permissions``),
never from the internal modules directly. Enforced by
``tests/test_identity_boundary.py``. Tests are exempt (they may probe
internals such as mock helpers and private RBAC maps).

Identity-owned files (may use internals directly):
``app/identity/*`` itself,
``app/core/security/firebase.py``, ``app/core/security/rbac.py``,
``app/domain/entities/user.py``,
``app/domain/repositories/user_repository.py``,
``app/application/services/auth_service.py``,
``app/application/dtos/auth_dtos.py``,
``app/infrastructure/persistence/models/{user,role,user_role}.py``,
``app/infrastructure/persistence/repositories/sql_user_repository.py``,
``app/api/deps.py``,
``app/api/v1/endpoints/{auth,users,identity_admin}.py`` (identity HTTP API),
``app/main.py`` (composition root).

This facade is the first step of the ARCHITECTURE.md microservices
extraction path: extracting Identity later means moving these
implementations behind this same interface.
"""

from __future__ import annotations

from app.api.deps import (
    get_ai_governance_user,
    get_analytics_user,
    get_chw_user,
    get_cms_user,
    get_current_active_user,
    get_current_admin,
    get_current_doctor,
    get_current_super_admin,
    get_current_user,
    get_interop_user,
    get_referral_user,
    get_sdg_export_user,
)
from app.application.dtos.auth_dtos import (
    AuthenticatedUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyTokenResponse,
)
from app.application.services.auth_service import AuthService
from app.core.security.firebase import (
    get_firebase_app,
    mock_email_for_uid,
    verify_firebase_token,
)
from app.core.security.rbac import (
    Permission,
    Role,
    check_permission,
    get_all_permissions,
    get_role_hierarchy,
    get_role_permissions,
    has_role,
)
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.identity.permissions import get_user_permissions
from app.identity.queries import (
    UserSummary,
    get_user_ids,
    get_user_summaries,
    get_user_summary,
)

__all__ = [
    "AuthService",
    "AuthenticatedUserResponse",
    "ForgotPasswordRequest",
    "LoginRequest",
    "LogoutResponse",
    "Permission",
    "RefreshTokenRequest",
    "RegisterRequest",
    "ResetPasswordRequest",
    "Role",
    "TokenResponse",
    "User",
    "UserRepository",
    "UserResponse",
    "UserSummary",
    "VerifyTokenResponse",
    "check_permission",
    "get_ai_governance_user",
    "get_all_permissions",
    "get_analytics_user",
    "get_chw_user",
    "get_cms_user",
    "get_current_active_user",
    "get_current_admin",
    "get_current_doctor",
    "get_current_super_admin",
    "get_current_user",
    "get_firebase_app",
    "get_interop_user",
    "get_referral_user",
    "get_role_hierarchy",
    "get_role_permissions",
    "get_sdg_export_user",
    "get_user_ids",
    "get_user_permissions",
    "get_user_summaries",
    "get_user_summary",
    "has_role",
    "mock_email_for_uid",
    "verify_firebase_token",
]
