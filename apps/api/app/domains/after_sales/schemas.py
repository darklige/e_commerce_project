from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.after_sales.models import (
    AfterSalesStatus,
    AfterSalesType,
    RefundStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)


class AfterSalesCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_item_id: UUID
    type: AfterSalesType
    quantity: int = Field(gt=0, le=100)
    refund_amount_cents: int = Field(gt=0)
    reason: str = Field(min_length=3, max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=10)
    idempotency_key: str = Field(min_length=8, max_length=160)


class AfterSalesSupplementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=3, max_length=3000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=10)
    idempotency_key: str = Field(min_length=8, max_length=160)


class MerchantReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=300)
    simulate_refund_success: bool = True
    refund_failure_reason: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=160)


class ReturnShipmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrier: str = Field(min_length=2, max_length=80)
    tracking_no: str = Field(min_length=4, max_length=80)
    idempotency_key: str = Field(min_length=8, max_length=160)


class CustomerEscalateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=300)
    priority: WorkOrderPriority = WorkOrderPriority.NORMAL
    idempotency_key: str = Field(min_length=8, max_length=160)


class CustomerCancelAfterSalesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=160)


class AdminDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(pattern=r"^(approve_refund|reject|require_merchant_review)$")
    reason: str = Field(min_length=3, max_length=300)
    simulate_refund_success: bool = True
    refund_failure_reason: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=160)


class AdminRefundRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=300)
    simulate_refund_success: bool = True
    refund_failure_reason: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=160)


class AutoProgressAfterSalesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    now: datetime | None = None
    limit: int = Field(default=50, ge=1, le=500)


class AutoProgressAfterSalesResponse(BaseModel):
    merchant_review_escalated: list[UUID]
    buyer_return_closed: list[UUID]
    merchant_receipt_refunded: list[UUID]


class RefundPublic(BaseModel):
    id: UUID
    after_sales_id: UUID
    status: RefundStatus
    amount_cents: int
    provider_refund_no: str
    failure_reason: str | None
    refunded_at: datetime | None
    created_at: datetime


class AfterSalesEventPublic(BaseModel):
    action: str
    from_status: AfterSalesStatus | None
    to_status: AfterSalesStatus
    idempotency_key: str | None
    reason: str | None
    created_at: datetime


class WorkOrderPublic(BaseModel):
    id: UUID
    work_order_no: str
    after_sales_id: UUID
    order_id: UUID
    customer_id: UUID
    merchant_id: UUID
    status: WorkOrderStatus
    priority: WorkOrderPriority
    reason: str
    queue: str
    evidence_summary: str | None
    internal_notes: str | None
    assigned_admin_id: UUID | None
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None


class AfterSalesPublic(BaseModel):
    id: UUID
    after_sales_no: str
    customer_id: UUID
    merchant_id: UUID
    order_id: UUID
    order_item_id: UUID
    type: AfterSalesType
    status: AfterSalesStatus
    reason: str
    description: str | None
    evidence_urls: list[str]
    quantity: int
    refund_amount_cents: int
    merchant_response_reason: str | None
    return_tracking_no: str | None
    return_carrier: str | None
    merchant_review_due_at: datetime
    buyer_return_due_at: datetime | None
    merchant_receipt_due_at: datetime | None
    refunded_at: datetime | None
    closed_reason: str | None
    created_at: datetime
    updated_at: datetime
    refunds: list[RefundPublic]
    events: list[AfterSalesEventPublic]
    work_order: WorkOrderPublic | None


class AfterSalesListResponse(BaseModel):
    items: list[AfterSalesPublic]
    total: int
    offset: int
    limit: int


class WorkOrderListResponse(BaseModel):
    items: list[WorkOrderPublic]
    total: int
    offset: int
    limit: int
