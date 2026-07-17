from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.domains.identity.constants import AccountType, Role

AUDIT_RESOURCE_ID_MAX_LENGTH = 320
AUDIT_USER_AGENT_MAX_LENGTH = 512


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True, max_length=320)
    display_name: str = Field(max_length=120)
    account_type: AccountType = Field(index=True)
    password_hash: str
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", "merchant_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    role: Role = Field(index=True)
    merchant_id: UUID | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    account_type: AccountType = Field(index=True)
    token_hash: str = Field(index=True, unique=True, max_length=64)
    expires_at: datetime = Field(index=True)
    consumed_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    actor_user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(index=True, max_length=120)
    resource_type: str = Field(index=True, max_length=80)
    resource_id: str | None = Field(
        default=None,
        index=True,
        max_length=AUDIT_RESOURCE_ID_MAX_LENGTH,
    )
    outcome: str = Field(index=True, max_length=40)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=AUDIT_USER_AGENT_MAX_LENGTH)
    reason: str | None = Field(default=None, sa_column=Column(Text))
    details: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now, index=True)
