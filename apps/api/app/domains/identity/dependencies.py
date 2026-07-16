from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.db.session import SessionDep
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission, Role
from app.domains.identity.models import User
from app.domains.identity.security import decode_access_token
from app.domains.identity.service import (
    get_permissions_for_roles,
    get_user_by_id,
    get_user_role_assignments,
)

bearer_scheme = HTTPBearer(auto_error=False)
SettingsDep = Annotated[Settings, Depends(get_settings)]
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


@dataclass(frozen=True)
class AuthContext:
    user: User
    roles: list[Role]
    permissions: list[Permission]
    merchant_ids: list[UUID]


def get_current_auth_context(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    credentials: BearerDep,
) -> AuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(settings, credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        write_audit_log(
            session,
            request=request,
            action="auth.token_rejected",
            resource_type="user",
            resource_id=str(user_id),
            outcome="failure",
            reason="missing or inactive user",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_assignments = get_user_role_assignments(session, user.id)
    roles = [assignment.role for assignment in role_assignments]
    permissions = get_permissions_for_roles(roles)
    merchant_ids = sorted(
        {assignment.merchant_id for assignment in role_assignments if assignment.merchant_id},
        key=str,
    )
    return AuthContext(user=user, roles=roles, permissions=permissions, merchant_ids=merchant_ids)


AuthContextDep = Annotated[AuthContext, Depends(get_current_auth_context)]


def require_permissions(
    *required_permissions: Permission,
    account_types: tuple[AccountType, ...] | None = None,
):
    def dependency(request: Request, session: SessionDep, auth: AuthContextDep) -> AuthContext:
        if account_types is not None and auth.user.account_type not in account_types:
            write_audit_log(
                session,
                request=request,
                action="auth.permission_denied",
                resource_type="account_type",
                resource_id=auth.user.account_type,
                outcome="failure",
                actor_user_id=auth.user.id,
                reason="account type cannot access console",
            )
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="permission denied",
            )

        missing_permissions = [
            item for item in required_permissions if item not in auth.permissions
        ]
        if missing_permissions:
            write_audit_log(
                session,
                request=request,
                action="auth.permission_denied",
                resource_type="permission",
                resource_id=",".join(missing_permissions),
                outcome="failure",
                actor_user_id=auth.user.id,
                reason="missing permission",
            )
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="permission denied",
            )
        return auth

    return dependency
