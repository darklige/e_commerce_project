from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionDep
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission
from app.domains.identity.dependencies import AuthContext, require_permissions
from app.domains.identity.models import User
from app.domains.identity.schemas import (
    AdminRegisterRequest,
    ConsoleAccessResponse,
    CustomerRegisterRequest,
    LoginRequest,
    MerchantRegisterRequest,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RegistrationResponse,
    TokenResponse,
    UserPublic,
)
from app.domains.identity.security import create_access_token
from app.domains.identity.service import (
    DuplicateEmailError,
    InactiveAccountError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRoleAssignmentError,
    authenticate_user,
    create_admin_account,
    create_customer_account,
    create_merchant_account,
    create_password_reset_token,
    get_permissions_for_roles,
    get_user_roles,
    reset_password_with_token,
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


def build_user_public(session: Session, user: User) -> UserPublic:
    roles = get_user_roles(session, user.id)
    permissions = get_permissions_for_roles(roles)
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


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_customer(
    payload: CustomerRegisterRequest,
    request: Request,
    session: SessionDep,
) -> UserPublic:
    try:
        user = create_customer_account(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
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
    return build_user_public(session, user)


@router.post("/register/customer", status_code=status.HTTP_201_CREATED)
def register_customer_account(
    payload: CustomerRegisterRequest,
    request: Request,
    session: SessionDep,
) -> RegistrationResponse:
    user = register_customer(payload, request, session)
    return RegistrationResponse(
        user=user,
        console="customer",
        next_step="continue shopping from the user web surface",
    )


@router.post("/register/merchant", status_code=status.HTTP_201_CREATED)
def register_merchant_account(
    payload: MerchantRegisterRequest,
    request: Request,
    session: SessionDep,
) -> RegistrationResponse:
    try:
        user, merchant_id = create_merchant_account(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except DuplicateEmailError as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.register",
            resource_type="user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="duplicate merchant email",
            details=f"shop_name={payload.shop_name}",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email is already registered",
        ) from exc

    write_audit_log(
        session,
        request=request,
        action="auth.register",
        resource_type="merchant_user",
        resource_id=str(user.id),
        outcome="success",
        actor_user_id=user.id,
        details=f"shop_name={payload.shop_name}; merchant_id={merchant_id}",
    )
    session.commit()
    return RegistrationResponse(
        user=build_user_public(session, user),
        console="merchant",
        next_step="complete merchant onboarding and publish products",
        merchant_ids=[merchant_id],
    )


@router.post("/register/admin", status_code=status.HTTP_201_CREATED)
def register_admin_account(
    payload: AdminRegisterRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> RegistrationResponse:
    if payload.invite_code != settings.admin_registration_invite_code:
        write_audit_log(
            session,
            request=request,
            action="auth.register",
            resource_type="admin_user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="invalid admin invite code",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin registration requires a valid platform invite",
        )

    try:
        user = create_admin_account(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            role=payload.role,
        )
    except DuplicateEmailError as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.register",
            resource_type="admin_user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="duplicate admin email",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email is already registered",
        ) from exc
    except InvalidRoleAssignmentError as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.register",
            resource_type="admin_user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="invalid admin role",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="admin role is not allowed for self-service registration",
        ) from exc

    write_audit_log(
        session,
        request=request,
        action="auth.register",
        resource_type="admin_user",
        resource_id=str(user.id),
        outcome="success",
        actor_user_id=user.id,
        details=f"role={payload.role}",
    )
    session.commit()
    return RegistrationResponse(
        user=build_user_public(session, user),
        console="admin",
        next_step="sign in to the admin console with the invited role",
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


@router.post("/password/forgot")
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> PasswordResetRequestResponse:
    user, reset_token, _expires_at = create_password_reset_token(
        session,
        email=payload.email,
        account_type=payload.account_type,
    )
    write_audit_log(
        session,
        request=request,
        action="auth.password_reset_request",
        resource_type="user",
        resource_id=str(user.id) if user else payload.email.lower(),
        outcome="accepted",
        actor_user_id=user.id if user else None,
        reason=f"{payload.account_type} password reset requested",
    )
    session.commit()
    return PasswordResetRequestResponse(
        account_type=payload.account_type,
        message="If the account exists, password reset instructions have been sent.",
        reset_token=reset_token if settings.app_env != "production" else None,
    )


@router.post("/password/reset")
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    session: SessionDep,
) -> PasswordResetConfirmResponse:
    try:
        user = reset_password_with_token(
            session,
            email=payload.email,
            account_type=payload.account_type,
            reset_token=payload.reset_token,
            new_password=payload.new_password,
        )
    except InvalidPasswordResetTokenError as exc:
        write_audit_log(
            session,
            request=request,
            action="auth.password_reset",
            resource_type="user",
            resource_id=payload.email.lower(),
            outcome="failure",
            reason="invalid or expired token",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password reset token is invalid or expired",
        ) from exc

    write_audit_log(
        session,
        request=request,
        action="auth.password_reset",
        resource_type="user",
        resource_id=str(user.id),
        outcome="success",
        actor_user_id=user.id,
    )
    session.commit()
    return PasswordResetConfirmResponse(
        account_type=payload.account_type,
        message="Password has been reset. Please sign in again.",
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
