from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.identity.constants import AccountType, Permission, Role


class CustomerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class MerchantRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    shop_name: str = Field(min_length=2, max_length=120)


class AdminRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    invite_code: str = Field(min_length=8, max_length=120)
    role: Role = Role.ADMIN_CUSTOMER_SERVICE


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


class RegistrationResponse(BaseModel):
    user: UserPublic
    console: str
    next_step: str
    merchant_ids: list[UUID] = Field(default_factory=list)


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    account_type: AccountType


class PasswordResetRequestResponse(BaseModel):
    accepted: bool = True
    account_type: AccountType
    delivery_channel: str = "email"
    message: str
    reset_token: str | None = None
    expires_in_minutes: int = 30


class PasswordResetConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    account_type: AccountType
    reset_token: str = Field(min_length=32, max_length=160)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetConfirmResponse(BaseModel):
    updated: bool = True
    account_type: AccountType
    message: str
