from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.identity.constants import AccountType, Permission, Role


class CustomerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    account_type: AccountType


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    account_type: AccountType
    is_active: bool
    roles: list[Role]
    permissions: list[Permission]
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserPublic


class ConsoleAccessResponse(BaseModel):
    user: UserPublic
    console: str
    allowed: bool
    merchant_ids: list[UUID] = Field(default_factory=list)
