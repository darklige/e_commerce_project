from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.order.models import OrderCloseReason, OrderStatus, PaymentStatus


class CartItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku_id: UUID
    quantity: int = Field(gt=0, le=100)
    selected: bool = True


class CartItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int | None = Field(default=None, gt=0, le=100)
    selected: bool | None = None


class CartItemPublic(BaseModel):
    id: UUID
    sku_id: UUID
    product_id: UUID
    merchant_id: UUID
    title: str
    subtitle: str | None
    sku_spec_name: str
    main_image_url: str | None
    unit_price_cents: int
    quantity: int
    selected: bool
    available: int
    line_total_cents: int
    warning: str | None = None


class CartResponse(BaseModel):
    items: list[CartItemPublic]
    selected_count: int
    selected_total_cents: int


class CheckoutPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cart_item_ids: list[UUID] | None = None


class CheckoutMerchantGroup(BaseModel):
    merchant_id: UUID
    items: list[CartItemPublic]
    subtotal_cents: int


class CheckoutPreviewResponse(BaseModel):
    groups: list[CheckoutMerchantGroup]
    items_total_cents: int
    shipping_fee_cents: int
    payable_total_cents: int
    can_submit: bool
    blockers: list[str]


class ShippingAddressSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receiver_name: str = Field(min_length=1, max_length=80)
    receiver_phone: str = Field(min_length=3, max_length=40)
    address: str = Field(min_length=5, max_length=500)


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=160)
    shipping_address: ShippingAddressSnapshot
    cart_item_ids: list[UUID] | None = None


class OrderItemPublic(BaseModel):
    id: UUID
    merchant_id: UUID
    product_id: UUID
    sku_id: UUID
    product_title: str
    sku_spec_name: str
    sku_code: str
    product_image_url: str | None
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class OrderTimelineEvent(BaseModel):
    action: str
    from_status: OrderStatus | None
    to_status: OrderStatus
    reason: str | None
    created_at: datetime


class OrderPublic(BaseModel):
    id: UUID
    order_no: str
    customer_id: UUID
    status: OrderStatus
    items_total_cents: int
    shipping_fee_cents: int
    payable_total_cents: int
    currency: str
    receiver_name: str
    receiver_phone: str
    shipping_address: str
    close_reason: OrderCloseReason | None
    close_note: str | None
    paid_at: datetime | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemPublic]
    timeline: list[OrderTimelineEvent]


class OrderListResponse(BaseModel):
    items: list[OrderPublic]
    total: int
    offset: int
    limit: int


class OrderCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=300)


class SimulatedPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=160)
    succeed: bool = True
    failure_reason: str | None = Field(default=None, max_length=300)


class PaymentPublic(BaseModel):
    id: UUID
    order_id: UUID
    status: PaymentStatus
    amount_cents: int
    provider_trade_no: str
    paid_at: datetime | None
    order: OrderPublic


class ExpireOrdersRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    now: datetime | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ExpireOrdersResponse(BaseModel):
    expired_order_ids: list[UUID]
    count: int
