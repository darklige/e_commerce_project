from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.db.session import SessionDep
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission
from app.domains.identity.dependencies import AuthContext, require_permissions
from app.domains.identity.schemas import (
    ConsoleAccessResponse,
    CustomerRegisterRequest,
    LoginRequest,
    TokenResponse,
    UserPublic,
)
from app.domains.identity.security import create_access_token
from app.domains.identity.service import (
    DuplicateEmailError,
    InactiveAccountError,
    InvalidCredentialsError,
    authenticate_user,
    create_user,
    get_permissions_for_roles,
    get_user_roles,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]

router = APIRouter(prefix="/auth", tags=["auth"])


def to_user_public(auth: AuthContext) -> UserPublic:
    return UserPublic(
        id=auth.user.id,
        email=auth.user.email,
        display_name=auth.user.display_name,
        account_type=auth.user.account_type,
        is_active=auth.user.is_active,
        roles=auth.roles,
        permissions=auth.permissions,
        created_at=auth.user.created_at,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_customer(
    payload: CustomerRegisterRequest,
    request: Request,
    session: SessionDep,
) -> UserPublic:
    try:
        user = create_user(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            account_type=AccountType.CUSTOMER,
        )
    except DuplicateEmailError as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.register",
            resource_type="user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="duplicate email",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email is already registered",
        ) from exc

    roles = get_user_roles(session, user.id)
    permissions = get_permissions_for_roles(roles)
    write_audit_log(
        session,
        request=request,
        action="auth.register",
        resource_type="user",
        resource_id=str(user.id),
        outcome="success",
        actor_user_id=user.id,
    )
    session.commit()
    return UserPublic(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        account_type=user.account_type,
        is_active=user.is_active,
        roles=roles,
        permissions=permissions,
        created_at=user.created_at,
    )


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> TokenResponse:
    try:
        user = authenticate_user(
            session,
            email=payload.email,
            password=payload.password,
            account_type=payload.account_type,
        )
    except (InvalidCredentialsError, InactiveAccountError) as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.login",
            resource_type="user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="invalid credentials or inactive account",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    roles = get_user_roles(session, user.id)
    permissions = get_permissions_for_roles(roles)
    token, expires_in_seconds = create_access_token(settings, user.id, user.account_type)
    write_audit_log(
        session,
        request=request,
        action="auth.login",
        resource_type="user",
        resource_id=str(user.id),
        outcome="success",
        actor_user_id=user.id,
    )
    session.commit()
    return TokenResponse(
        access_token=token,
        expires_in_seconds=expires_in_seconds,
        user=UserPublic(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            account_type=user.account_type,
            is_active=user.is_active,
            roles=roles,
            permissions=permissions,
            created_at=user.created_at,
        ),
    )


@router.get("/me")
def read_me(
    auth: Annotated[AuthContext, Depends(require_permissions(Permission.USER_PROFILE_READ))],
) -> UserPublic:
    return to_user_public(auth)


@router.get("/admin/me")
def read_admin_me(
    auth: Annotated[
        AuthContext,
        Depends(
            require_permissions(
                Permission.ADMIN_CONSOLE_ACCESS,
                account_types=(AccountType.ADMIN,),
            )
        ),
    ],
) -> ConsoleAccessResponse:
    return ConsoleAccessResponse(user=to_user_public(auth), console="admin", allowed=True)


@router.get("/merchant/me")
def read_merchant_me(
    auth: Annotated[
        AuthContext,
        Depends(
            require_permissions(
                Permission.MERCHANT_CONSOLE_ACCESS,
                account_types=(AccountType.MERCHANT,),
            )
        ),
    ],
) -> ConsoleAccessResponse:
    return ConsoleAccessResponse(
        user=to_user_public(auth),
        console="merchant",
        allowed=True,
        merchant_ids=auth.merchant_ids,
    )
