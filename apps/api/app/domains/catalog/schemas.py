from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.catalog.models import ProductStatus, ReservationStatus


class CategoryPublic(BaseModel):
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")
    parent_id: UUID | None = None
    sort_order: int = 0


class BrandPublic(BaseModel):
    id: UUID
    name: str
    slug: str


class BrandCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")


class SkuCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku_code: str = Field(min_length=1, max_length=80)
    spec_name: str = Field(min_length=1, max_length=160)
    price_cents: int = Field(ge=0)
    list_price_cents: int | None = Field(default=None, ge=0)
    initial_stock: int = Field(default=0, ge=0)


class SkuPublic(BaseModel):
    id: UUID
    sku_code: str
    spec_name: str
    price_cents: int
    list_price_cents: int | None
    is_active: bool
    on_hand: int
    reserved: int
    available: int


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID
    brand_id: UUID | None = None
    title: str = Field(min_length=1, max_length=180)
    subtitle: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    main_image_url: str | None = Field(default=None, max_length=600)
    skus: list[SkuCreate] = Field(min_length=1)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID | None = None
    brand_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=180)
    subtitle: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    main_image_url: str | None = Field(default=None, max_length=600)


class SkuUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_name: str | None = Field(default=None, min_length=1, max_length=160)
    price_cents: int | None = Field(default=None, ge=0)
    list_price_cents: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductListItem(BaseModel):
    id: UUID
    merchant_id: UUID
    category_id: UUID
    brand_id: UUID | None
    title: str
    subtitle: str | None
    status: ProductStatus
    main_image_url: str | None
    min_price_cents: int
    max_price_cents: int
    total_available: int
    created_at: datetime
    updated_at: datetime


class ProductDetail(ProductListItem):
    description: str | None
    skus: list[SkuPublic]


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    total: int
    offset: int
    limit: int


class InventoryAdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku_id: UUID
    delta: int = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=3, max_length=300)


class InventoryReservationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku_id: UUID
    quantity: int = Field(gt=0, le=100000)
    idempotency_key: str = Field(min_length=8, max_length=160)


class InventoryReservationResponse(BaseModel):
    reservation_id: UUID
    sku_id: UUID
    quantity: int
    status: ReservationStatus
    available: int
