from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProductStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    ARCHIVED = "archived"


class ReservationStatus(StrEnum):
    RESERVED = "reserved"
    RELEASED = "released"
    CONSUMED = "consumed"


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120, index=True)
    slug: str = Field(max_length=120, index=True, unique=True)
    parent_id: UUID | None = Field(default=None, foreign_key="categories.id", index=True)
    is_active: bool = Field(default=True, index=True)
    sort_order: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Brand(SQLModel, table=True):
    __tablename__ = "brands"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120, index=True)
    slug: str = Field(max_length=120, index=True, unique=True)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Product(SQLModel, table=True):
    __tablename__ = "spus"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(index=True)
    category_id: UUID = Field(foreign_key="categories.id", index=True)
    brand_id: UUID | None = Field(default=None, foreign_key="brands.id", index=True)
    title: str = Field(max_length=180, index=True)
    subtitle: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, sa_column=Column(Text))
    status: ProductStatus = Field(default=ProductStatus.DRAFT, index=True)
    main_image_url: str | None = Field(default=None, max_length=600)
    min_price_cents: int = Field(default=0, ge=0, index=True)
    max_price_cents: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Sku(SQLModel, table=True):
    __tablename__ = "skus"
    __table_args__ = (UniqueConstraint("merchant_id", "sku_code"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    spu_id: UUID = Field(foreign_key="spus.id", index=True)
    merchant_id: UUID = Field(index=True)
    sku_code: str = Field(max_length=80, index=True)
    spec_name: str = Field(max_length=160)
    price_cents: int = Field(ge=0, index=True)
    list_price_cents: int | None = Field(default=None, ge=0)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SkuInventory(SQLModel, table=True):
    __tablename__ = "sku_inventory"

    sku_id: UUID = Field(foreign_key="skus.id", primary_key=True)
    merchant_id: UUID = Field(index=True)
    on_hand: int = Field(default=0, ge=0)
    reserved: int = Field(default=0, ge=0)
    version: int = Field(default=0)
    updated_at: datetime = Field(default_factory=utc_now)


class InventoryReservation(SQLModel, table=True):
    __tablename__ = "inventory_reservations"
    __table_args__ = (UniqueConstraint("merchant_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sku_id: UUID = Field(foreign_key="skus.id", index=True)
    merchant_id: UUID = Field(index=True)
    idempotency_key: str = Field(max_length=160, index=True)
    quantity: int = Field(gt=0)
    status: ReservationStatus = Field(default=ReservationStatus.RESERVED, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
