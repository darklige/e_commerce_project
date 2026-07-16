from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


def default_order_expires_at() -> datetime:
    return utc_now() + timedelta(minutes=30)


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PAID_PENDING_SHIPMENT = "paid_pending_shipment"
    SHIPPED_AWAITING_RECEIPT = "shipped_awaiting_receipt"
    COMPLETED = "completed"
    CLOSED = "closed"


class OrderCloseReason(StrEnum):
    CUSTOMER_CANCELLED = "customer_cancelled"
    PAYMENT_TIMEOUT = "payment_timeout"
    PAYMENT_FAILED = "payment_failed"
    RISK_CONTROL = "risk_control"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentProvider(StrEnum):
    SIMULATED = "simulated"


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("customer_id", "sku_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    sku_id: UUID = Field(foreign_key="skus.id", index=True)
    quantity: int = Field(gt=0)
    selected: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("customer_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_no: str = Field(max_length=40, index=True, unique=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING_PAYMENT, index=True)
    idempotency_key: str = Field(max_length=160, index=True)
    request_signature: str = Field(max_length=64)
    items_total_cents: int = Field(ge=0)
    shipping_fee_cents: int = Field(default=0, ge=0)
    payable_total_cents: int = Field(ge=0)
    currency: str = Field(default="CNY", max_length=8)
    receiver_name: str = Field(max_length=80)
    receiver_phone: str = Field(max_length=40)
    shipping_address: str = Field(max_length=500)
    close_reason: OrderCloseReason | None = Field(default=None, index=True)
    close_note: str | None = Field(default=None, max_length=300)
    paid_at: datetime | None = Field(default=None, index=True)
    expires_at: datetime = Field(default_factory=default_order_expires_at, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    merchant_id: UUID = Field(index=True)
    product_id: UUID = Field(foreign_key="spus.id", index=True)
    sku_id: UUID = Field(foreign_key="skus.id", index=True)
    reservation_id: UUID = Field(foreign_key="inventory_reservations.id", index=True)
    product_title: str = Field(max_length=180)
    sku_spec_name: str = Field(max_length=160)
    sku_code: str = Field(max_length=80)
    product_image_url: str | None = Field(default=None, max_length=600)
    unit_price_cents: int = Field(ge=0)
    quantity: int = Field(gt=0)
    line_total_cents: int = Field(ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class OrderStatusEvent(SQLModel, table=True):
    __tablename__ = "order_status_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    actor_user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    from_status: OrderStatus | None = Field(default=None, index=True)
    to_status: OrderStatus = Field(index=True)
    action: str = Field(max_length=80, index=True)
    reason: str | None = Field(default=None, max_length=300)
    details: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now, index=True)


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("order_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    provider: PaymentProvider = Field(default=PaymentProvider.SIMULATED, index=True)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)
    idempotency_key: str = Field(max_length=160, index=True)
    amount_cents: int = Field(ge=0)
    provider_trade_no: str = Field(max_length=80, index=True)
    failure_reason: str | None = Field(default=None, max_length=300)
    paid_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)
