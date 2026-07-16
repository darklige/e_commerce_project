from uuid import UUID

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
from app.domains.identity.models import User, UserRole
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
