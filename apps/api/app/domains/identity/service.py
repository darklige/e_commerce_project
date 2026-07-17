from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.domains.identity.constants import (
    ACCOUNT_DEFAULT_ROLE,
    ROLE_ACCOUNT_TYPES,
    ROLE_PERMISSIONS,
    AccountType,
    Permission,
    Role,
)
from app.domains.identity.models import PasswordResetToken, User, UserRole
from app.domains.identity.security import hash_password, verify_password


class IdentityError(Exception):
    pass


class DuplicateEmailError(IdentityError):
    pass


class InvalidCredentialsError(IdentityError):
    pass


class InactiveAccountError(IdentityError):
    pass


class InvalidRoleAssignmentError(IdentityError):
    pass


class InvalidPasswordResetTokenError(IdentityError):
    pass


PUBLIC_ADMIN_REGISTRATION_ROLES = {
    Role.ADMIN_OPERATOR,
    Role.ADMIN_CUSTOMER_SERVICE,
    Role.ADMIN_CUSTOMER_SERVICE_LEAD,
    Role.ADMIN_RISK,
    Role.ADMIN_FINANCE,
    Role.ADMIN_TECH,
    Role.AUDIT_READONLY,
}


def create_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    account_type: AccountType,
    roles: list[Role] | None = None,
    merchant_id: UUID | None = None,
) -> User:
    assigned_roles = roles or [ACCOUNT_DEFAULT_ROLE[account_type]]
    validate_role_assignments(
        account_type=account_type,
        roles=assigned_roles,
        merchant_id=merchant_id,
    )
    user = User(
        email=email.lower(),
        display_name=display_name,
        account_type=account_type,
        password_hash=hash_password(password),
    )
    try:
        session.add(user)
        session.flush()

        for role in assigned_roles:
            session.add(UserRole(user_id=user.id, role=role, merchant_id=merchant_id))

        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateEmailError("email is already registered") from exc

    session.refresh(user)
    return user


def create_customer_account(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
) -> User:
    return create_user(
        session,
        email=email,
        password=password,
        display_name=display_name,
        account_type=AccountType.CUSTOMER,
    )


def create_merchant_account(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User, UUID]:
    merchant_id = uuid4()
    user = create_user(
        session,
        email=email,
        password=password,
        display_name=display_name,
        account_type=AccountType.MERCHANT,
        roles=[Role.MERCHANT_OWNER],
        merchant_id=merchant_id,
    )
    return user, merchant_id


def create_admin_account(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    role: Role,
) -> User:
    if role not in PUBLIC_ADMIN_REGISTRATION_ROLES:
        raise InvalidRoleAssignmentError("admin registration role is not allowed")
    return create_user(
        session,
        email=email,
        password=password,
        display_name=display_name,
        account_type=AccountType.ADMIN,
        roles=[role],
    )


def validate_role_assignments(
    *,
    account_type: AccountType,
    roles: list[Role],
    merchant_id: UUID | None,
) -> None:
    if account_type != AccountType.MERCHANT and merchant_id is not None:
        raise InvalidRoleAssignmentError("merchant scope is only valid for merchant accounts")

    for role in roles:
        allowed_account_types = ROLE_ACCOUNT_TYPES[role]
        if account_type not in allowed_account_types:
            raise InvalidRoleAssignmentError(
                f"role {role} cannot be assigned to {account_type} accounts"
            )
        if account_type == AccountType.MERCHANT and merchant_id is None:
            raise InvalidRoleAssignmentError("merchant accounts require a merchant scope")


def authenticate_user(
    session: Session,
    *,
    email: str,
    password: str,
    account_type: AccountType,
) -> User:
    user = get_user_by_email(session, email)
    if user is None or user.account_type != account_type:
        raise InvalidCredentialsError("invalid credentials")
    if not user.is_active:
        raise InactiveAccountError("account is inactive")
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid credentials")
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def get_user_roles(session: Session, user_id: UUID) -> list[Role]:
    return [row.role for row in get_user_role_assignments(session, user_id)]


def get_user_role_assignments(session: Session, user_id: UUID) -> list[UserRole]:
    statement = select(UserRole).where(UserRole.user_id == user_id)
    return list(session.exec(statement).all())


def get_permissions_for_roles(roles: list[Role]) -> list[Permission]:
    permissions: set[Permission] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS[role])
    return sorted(permissions)


def create_password_reset_token(
    session: Session,
    *,
    email: str,
    account_type: AccountType,
    expires_in_minutes: int = 30,
) -> tuple[User | None, str | None, datetime | None]:
    user = get_user_by_email(session, email)
    if user is None or user.account_type != account_type or not user.is_active:
        return None, None, None

    reset_token = token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)
    session.add(
        PasswordResetToken(
            user_id=user.id,
            account_type=account_type,
            token_hash=hash_reset_token(reset_token),
            expires_at=expires_at,
        )
    )
    session.commit()
    return user, reset_token, expires_at


def reset_password_with_token(
    session: Session,
    *,
    email: str,
    account_type: AccountType,
    reset_token: str,
    new_password: str,
) -> User:
    user = get_user_by_email(session, email)
    if user is None or user.account_type != account_type or not user.is_active:
        raise InvalidPasswordResetTokenError("password reset token is invalid or expired")

    token_hash = hash_reset_token(reset_token)
    statement = (
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .where(PasswordResetToken.account_type == account_type)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.consumed_at.is_(None))
    )
    password_reset = session.exec(statement).first()
    now = datetime.now(UTC)
    if password_reset is None or normalize_datetime(password_reset.expires_at) < now:
        raise InvalidPasswordResetTokenError("password reset token is invalid or expired")

    user.password_hash = hash_password(new_password)
    user.updated_at = now
    password_reset.consumed_at = now
    session.add(user)
    session.add(password_reset)
    session.commit()
    session.refresh(user)
    return user


def hash_reset_token(reset_token: str) -> str:
    return sha256(reset_token.encode("utf-8")).hexdigest()


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
