from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


def merchant_review_deadline() -> datetime:
    return utc_now() + timedelta(hours=48)


def buyer_return_deadline() -> datetime:
    return utc_now() + timedelta(days=7)


def merchant_receipt_deadline() -> datetime:
    return utc_now() + timedelta(hours=72)


class AfterSalesType(StrEnum):
    REFUND_ONLY = "refund_only"
    RETURN_REFUND = "return_refund"


class AfterSalesStatus(StrEnum):
    MERCHANT_REVIEW = "merchant_review"
    REJECTED = "rejected"
    WAITING_BUYER_RETURN = "waiting_buyer_return"
    WAITING_MERCHANT_RECEIPT = "waiting_merchant_receipt"
    REFUNDING = "refunding"
    REFUNDED = "refunded"
    REFUND_FAILED = "refund_failed"
    CUSTOMER_SERVICE = "customer_service"
    CLOSED = "closed"


class RefundStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


class WorkOrderStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"


class WorkOrderPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class AfterSalesRequest(SQLModel, table=True):
    __tablename__ = "after_sales_requests"
    __table_args__ = (UniqueConstraint("customer_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    after_sales_no: str = Field(max_length=40, index=True, unique=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    merchant_id: UUID = Field(index=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    order_item_id: UUID = Field(foreign_key="order_items.id", index=True)
    type: AfterSalesType = Field(index=True)
    status: AfterSalesStatus = Field(default=AfterSalesStatus.MERCHANT_REVIEW, index=True)
    idempotency_key: str = Field(max_length=160, index=True)
    request_signature: str = Field(max_length=64)
    reason: str = Field(max_length=300)
    description: str | None = Field(default=None, sa_column=Column(Text))
    evidence_urls: str | None = Field(default=None, sa_column=Column(Text))
    quantity: int = Field(gt=0)
    refund_amount_cents: int = Field(ge=0)
    merchant_response_reason: str | None = Field(default=None, sa_column=Column(Text))
    return_tracking_no: str | None = Field(default=None, max_length=80)
    return_carrier: str | None = Field(default=None, max_length=80)
    merchant_review_due_at: datetime = Field(default_factory=merchant_review_deadline, index=True)
    buyer_return_due_at: datetime | None = Field(default=None, index=True)
    merchant_receipt_due_at: datetime | None = Field(default=None, index=True)
    refunded_at: datetime | None = Field(default=None, index=True)
    closed_reason: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class AfterSalesEvent(SQLModel, table=True):
    __tablename__ = "after_sales_events"
    __table_args__ = (UniqueConstraint("after_sales_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    after_sales_id: UUID = Field(foreign_key="after_sales_requests.id", index=True)
    actor_user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    from_status: AfterSalesStatus | None = Field(default=None, index=True)
    to_status: AfterSalesStatus = Field(index=True)
    action: str = Field(max_length=100, index=True)
    idempotency_key: str | None = Field(default=None, max_length=160, index=True)
    reason: str | None = Field(default=None, max_length=300)
    details: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now, index=True)


class Refund(SQLModel, table=True):
    __tablename__ = "refunds"
    __table_args__ = (UniqueConstraint("after_sales_id", "idempotency_key"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    after_sales_id: UUID = Field(foreign_key="after_sales_requests.id", index=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payments.id", index=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    merchant_id: UUID = Field(index=True)
    status: RefundStatus = Field(default=RefundStatus.PENDING, index=True)
    idempotency_key: str = Field(max_length=160, index=True)
    amount_cents: int = Field(ge=0)
    provider_refund_no: str = Field(max_length=80, index=True)
    failure_reason: str | None = Field(default=None, max_length=300)
    refunded_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class WorkOrder(SQLModel, table=True):
    __tablename__ = "work_orders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    work_order_no: str = Field(max_length=40, index=True, unique=True)
    after_sales_id: UUID = Field(foreign_key="after_sales_requests.id", index=True)
    order_id: UUID = Field(foreign_key="orders.id", index=True)
    customer_id: UUID = Field(foreign_key="users.id", index=True)
    merchant_id: UUID = Field(index=True)
    status: WorkOrderStatus = Field(default=WorkOrderStatus.OPEN, index=True)
    priority: WorkOrderPriority = Field(default=WorkOrderPriority.NORMAL, index=True)
    reason: str = Field(max_length=300)
    queue: str = Field(default="customer_service", max_length=80, index=True)
    evidence_summary: str | None = Field(default=None, sa_column=Column(Text))
    internal_notes: str | None = Field(default=None, sa_column=Column(Text))
    assigned_admin_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    resolution: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None, index=True)
