import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.domains.after_sales.models import (
    AfterSalesEvent,
    AfterSalesRequest,
    AfterSalesStatus,
    AfterSalesType,
    Refund,
    RefundStatus,
    WorkOrder,
    WorkOrderPriority,
    WorkOrderStatus,
    buyer_return_deadline,
    merchant_receipt_deadline,
    merchant_review_deadline,
    utc_now,
)
from app.domains.after_sales.schemas import (
    AdminDecisionRequest,
    AdminRefundRetryRequest,
    AfterSalesCreateRequest,
    AfterSalesEventPublic,
    AfterSalesListResponse,
    AfterSalesPublic,
    AfterSalesSupplementRequest,
    AutoProgressAfterSalesResponse,
    CustomerCancelAfterSalesRequest,
    CustomerEscalateRequest,
    MerchantReviewRequest,
    RefundPublic,
    ReturnShipmentRequest,
    WorkOrderListResponse,
    WorkOrderPublic,
)
from app.domains.after_sales.state_machine import (
    AfterSalesStateMachineError,
    assert_transition,
)
from app.domains.order.models import Order, OrderItem, OrderStatus, Payment, PaymentStatus


class AfterSalesError(Exception):
    pass


class AfterSalesNotFoundError(AfterSalesError):
    pass


class AfterSalesPermissionError(AfterSalesError):
    pass


class AfterSalesConflictError(AfterSalesError):
    pass


def create_after_sales_request(
    session: Session,
    customer_id: UUID,
    payload: AfterSalesCreateRequest,
) -> AfterSalesPublic:
    signature = build_create_signature(payload)
    existing = session.exec(
        select(AfterSalesRequest).where(
            AfterSalesRequest.customer_id == customer_id,
            AfterSalesRequest.idempotency_key == payload.idempotency_key,
        )
    ).first()
    if existing is not None:
        if existing.request_signature != signature:
            raise AfterSalesConflictError("idempotency key conflicts with another request")
        return build_after_sales_public(session, existing)

    order_item = require_order_item(session, payload.order_item_id)
    if order_item.customer_id != customer_id:
        raise AfterSalesPermissionError("order item belongs to another customer")
    order = require_order(session, order_item.order_id)
    validate_after_sales_order_status(order, payload.type)
    if payload.quantity > order_item.quantity:
        raise AfterSalesConflictError("after-sales quantity exceeds purchased quantity")
    if payload.refund_amount_cents > order_item.line_total_cents:
        raise AfterSalesConflictError("refund amount exceeds order item total")
    if has_open_after_sales_for_order_item(session, order_item.id):
        raise AfterSalesConflictError("order item already has an open after-sales request")

    now = utc_now()
    request = AfterSalesRequest(
        after_sales_no=generate_after_sales_no(now),
        customer_id=customer_id,
        merchant_id=order_item.merchant_id,
        order_id=order_item.order_id,
        order_item_id=order_item.id,
        type=payload.type,
        idempotency_key=payload.idempotency_key,
        request_signature=signature,
        reason=payload.reason,
        description=payload.description,
        evidence_urls=encode_evidence(payload.evidence_urls),
        quantity=payload.quantity,
        refund_amount_cents=payload.refund_amount_cents,
        created_at=now,
        updated_at=now,
    )
    session.add(request)
    flush_or_conflict(session, "after-sales request already exists")
    add_event(
        session,
        request,
        action="after_sales.create",
        actor_user_id=customer_id,
        from_status=None,
        to_status=AfterSalesStatus.MERCHANT_REVIEW,
        reason=payload.reason,
        details=payload.description,
    )
    commit_or_conflict(session, "after-sales request already exists")
    session.refresh(request)
    return build_after_sales_public(session, request)


def list_customer_after_sales(
    session: Session,
    customer_id: UUID,
    *,
    offset: int,
    limit: int,
) -> AfterSalesListResponse:
    total = session.exec(
        select(func.count())
        .select_from(AfterSalesRequest)
        .where(AfterSalesRequest.customer_id == customer_id)
    ).one()
    requests = session.exec(
        select(AfterSalesRequest)
        .where(AfterSalesRequest.customer_id == customer_id)
        .order_by(AfterSalesRequest.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return AfterSalesListResponse(
        items=[build_after_sales_public(session, item) for item in requests],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_customer_after_sales(
    session: Session,
    customer_id: UUID,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if request.customer_id != customer_id:
        raise AfterSalesPermissionError("after-sales request belongs to another customer")
    return build_after_sales_public(session, request)


def supplement_after_sales(
    session: Session,
    customer_id: UUID,
    after_sales_id: UUID,
    payload: AfterSalesSupplementRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if request.customer_id != customer_id:
        raise AfterSalesPermissionError("after-sales request belongs to another customer")
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.customer_supplement"},
    ):
        return build_after_sales_public(session, request)
    if request.status not in {AfterSalesStatus.REJECTED, AfterSalesStatus.MERCHANT_REVIEW}:
        raise AfterSalesConflictError("only rejected or reviewing requests can be supplemented")
    if request.status == AfterSalesStatus.REJECTED:
        transition(
            session,
            request,
            to_status=AfterSalesStatus.MERCHANT_REVIEW,
            actor_user_id=customer_id,
            action="after_sales.customer_supplement",
            reason="customer supplemented evidence",
            details=payload.description,
            idempotency_key=payload.idempotency_key,
        )
    else:
        add_event(
            session,
            request,
            action="after_sales.customer_supplement",
            actor_user_id=customer_id,
            from_status=request.status,
            to_status=request.status,
            reason="customer supplemented evidence",
            details=payload.description,
            idempotency_key=payload.idempotency_key,
        )
    request.description = merge_text(request.description, payload.description)
    request.evidence_urls = encode_evidence(
        decode_evidence(request.evidence_urls) + payload.evidence_urls
    )
    request.merchant_review_due_at = merchant_review_deadline()
    request.updated_at = utc_now()
    session.add(request)
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def submit_return_shipment(
    session: Session,
    customer_id: UUID,
    after_sales_id: UUID,
    payload: ReturnShipmentRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if request.customer_id != customer_id:
        raise AfterSalesPermissionError("after-sales request belongs to another customer")
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.return_shipped"},
    ):
        return build_after_sales_public(session, request)
    if request.status != AfterSalesStatus.WAITING_BUYER_RETURN:
        raise AfterSalesConflictError(
            "return shipment is only valid while waiting for buyer return"
        )
    request.return_carrier = payload.carrier
    request.return_tracking_no = payload.tracking_no
    request.merchant_receipt_due_at = merchant_receipt_deadline()
    transition(
        session,
        request,
        to_status=AfterSalesStatus.WAITING_MERCHANT_RECEIPT,
        actor_user_id=customer_id,
        action="after_sales.return_shipped",
        reason="buyer returned goods",
        details=f"{payload.carrier}:{payload.tracking_no}",
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def escalate_after_sales(
    session: Session,
    customer_id: UUID,
    after_sales_id: UUID,
    payload: CustomerEscalateRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if request.customer_id != customer_id:
        raise AfterSalesPermissionError("after-sales request belongs to another customer")
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.customer_escalate"},
    ):
        return build_after_sales_public(session, request)
    if request.status not in {
        AfterSalesStatus.MERCHANT_REVIEW,
        AfterSalesStatus.REJECTED,
        AfterSalesStatus.WAITING_BUYER_RETURN,
        AfterSalesStatus.WAITING_MERCHANT_RECEIPT,
        AfterSalesStatus.REFUND_FAILED,
    }:
        raise AfterSalesConflictError("current after-sales request cannot be escalated")
    ensure_work_order(session, request, payload.reason, priority=payload.priority)
    transition(
        session,
        request,
        to_status=AfterSalesStatus.CUSTOMER_SERVICE,
        actor_user_id=customer_id,
        action="after_sales.customer_escalate",
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def cancel_after_sales(
    session: Session,
    customer_id: UUID,
    after_sales_id: UUID,
    payload: CustomerCancelAfterSalesRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if request.customer_id != customer_id:
        raise AfterSalesPermissionError("after-sales request belongs to another customer")
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.customer_cancel"},
    ):
        return build_after_sales_public(session, request)
    if request.status not in {
        AfterSalesStatus.MERCHANT_REVIEW,
        AfterSalesStatus.REJECTED,
        AfterSalesStatus.WAITING_BUYER_RETURN,
    }:
        raise AfterSalesConflictError("current after-sales request cannot be cancelled by customer")
    request.closed_reason = payload.reason
    transition(
        session,
        request,
        to_status=AfterSalesStatus.CLOSED,
        actor_user_id=customer_id,
        action="after_sales.customer_cancel",
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def list_merchant_after_sales(
    session: Session,
    merchant_ids: list[UUID],
    *,
    offset: int,
    limit: int,
) -> AfterSalesListResponse:
    if not merchant_ids:
        raise AfterSalesPermissionError("merchant scope required")
    total = session.exec(
        select(func.count())
        .select_from(AfterSalesRequest)
        .where(col(AfterSalesRequest.merchant_id).in_(merchant_ids))
    ).one()
    requests = session.exec(
        select(AfterSalesRequest)
        .where(col(AfterSalesRequest.merchant_id).in_(merchant_ids))
        .order_by(AfterSalesRequest.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return AfterSalesListResponse(
        items=[build_after_sales_public(session, item) for item in requests],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_merchant_after_sales(
    session: Session,
    merchant_ids: list[UUID],
    after_sales_id: UUID,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    require_merchant_scope(request, merchant_ids)
    return build_after_sales_public(session, request)


def merchant_approve_after_sales(
    session: Session,
    merchant_ids: list[UUID],
    actor_user_id: UUID,
    after_sales_id: UUID,
    payload: MerchantReviewRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    require_merchant_scope(request, merchant_ids)
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.merchant_approve_return", "after_sales.merchant_approve_refund"},
    ):
        return build_after_sales_public(session, request)
    if request.status != AfterSalesStatus.MERCHANT_REVIEW:
        raise AfterSalesConflictError("only merchant review requests can be approved")
    request.merchant_response_reason = payload.reason
    if request.type == AfterSalesType.RETURN_REFUND:
        request.buyer_return_due_at = buyer_return_deadline()
        transition(
            session,
            request,
            to_status=AfterSalesStatus.WAITING_BUYER_RETURN,
            actor_user_id=actor_user_id,
            action="after_sales.merchant_approve_return",
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    else:
        start_refund(
            session,
            request,
            actor_user_id=actor_user_id,
            action="after_sales.merchant_approve_refund",
            reason=payload.reason,
            simulate_success=payload.simulate_refund_success,
            failure_reason=payload.refund_failure_reason,
            idempotency_key=payload.idempotency_key,
        )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def merchant_reject_after_sales(
    session: Session,
    merchant_ids: list[UUID],
    actor_user_id: UUID,
    after_sales_id: UUID,
    payload: MerchantReviewRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    require_merchant_scope(request, merchant_ids)
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.merchant_reject"},
    ):
        return build_after_sales_public(session, request)
    if request.status != AfterSalesStatus.MERCHANT_REVIEW:
        raise AfterSalesConflictError("only merchant review requests can be rejected")
    request.merchant_response_reason = payload.reason
    transition(
        session,
        request,
        to_status=AfterSalesStatus.REJECTED,
        actor_user_id=actor_user_id,
        action="after_sales.merchant_reject",
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def merchant_confirm_receipt(
    session: Session,
    merchant_ids: list[UUID],
    actor_user_id: UUID,
    after_sales_id: UUID,
    payload: MerchantReviewRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    require_merchant_scope(request, merchant_ids)
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.merchant_confirm_receipt"},
    ):
        return build_after_sales_public(session, request)
    if request.status != AfterSalesStatus.WAITING_MERCHANT_RECEIPT:
        raise AfterSalesConflictError("merchant can confirm receipt only after buyer shipment")
    start_refund(
        session,
        request,
        actor_user_id=actor_user_id,
        action="after_sales.merchant_confirm_receipt",
        reason=payload.reason,
        simulate_success=payload.simulate_refund_success,
        failure_reason=payload.refund_failure_reason,
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def list_admin_after_sales(
    session: Session,
    *,
    offset: int,
    limit: int,
) -> AfterSalesListResponse:
    total = session.exec(select(func.count()).select_from(AfterSalesRequest)).one()
    requests = session.exec(
        select(AfterSalesRequest)
        .order_by(AfterSalesRequest.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return AfterSalesListResponse(
        items=[build_after_sales_public(session, item) for item in requests],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_admin_after_sales(session: Session, after_sales_id: UUID) -> AfterSalesPublic:
    return build_after_sales_public(session, require_after_sales(session, after_sales_id))


def admin_decide_after_sales(
    session: Session,
    actor_user_id: UUID,
    after_sales_id: UUID,
    payload: AdminDecisionRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {
            "after_sales.admin_approve_refund",
            "after_sales.admin_reject",
            "after_sales.admin_require_merchant_review",
        },
    ):
        return build_after_sales_public(session, request)
    work_order = ensure_work_order(
        session,
        request,
        payload.reason,
        priority=WorkOrderPriority.HIGH,
        assigned_admin_id=actor_user_id,
    )
    if request.status not in {AfterSalesStatus.CUSTOMER_SERVICE, AfterSalesStatus.REFUND_FAILED}:
        transition(
            session,
            request,
            to_status=AfterSalesStatus.CUSTOMER_SERVICE,
            actor_user_id=actor_user_id,
            action="after_sales.admin_takeover",
            reason=payload.reason,
        )

    if payload.decision == "approve_refund":
        start_refund(
            session,
            request,
            actor_user_id=actor_user_id,
            action="after_sales.admin_approve_refund",
            reason=payload.reason,
            simulate_success=payload.simulate_refund_success,
            failure_reason=payload.refund_failure_reason,
            idempotency_key=payload.idempotency_key,
        )
        resolve_work_order(session, work_order, actor_user_id, "approved refund")
    elif payload.decision == "reject":
        request.closed_reason = payload.reason
        transition(
            session,
            request,
            to_status=AfterSalesStatus.CLOSED,
            actor_user_id=actor_user_id,
            action="after_sales.admin_reject",
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
        resolve_work_order(session, work_order, actor_user_id, "rejected by customer service")
    else:
        transition(
            session,
            request,
            to_status=AfterSalesStatus.MERCHANT_REVIEW,
            actor_user_id=actor_user_id,
            action="after_sales.admin_require_merchant_review",
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def retry_refund(
    session: Session,
    actor_user_id: UUID,
    after_sales_id: UUID,
    payload: AdminRefundRetryRequest,
) -> AfterSalesPublic:
    request = require_after_sales(session, after_sales_id)
    if has_idempotent_event(
        session,
        request,
        payload.idempotency_key,
        {"after_sales.admin_retry_refund"},
    ):
        return build_after_sales_public(session, request)
    if request.status != AfterSalesStatus.REFUND_FAILED:
        raise AfterSalesConflictError("only failed refunds can be retried")
    start_refund(
        session,
        request,
        actor_user_id=actor_user_id,
        action="after_sales.admin_retry_refund",
        reason=payload.reason,
        simulate_success=payload.simulate_refund_success,
        failure_reason=payload.refund_failure_reason,
        idempotency_key=payload.idempotency_key,
    )
    commit_or_conflict(session, "after-sales action was already processed")
    session.refresh(request)
    return build_after_sales_public(session, request)


def list_work_orders(
    session: Session,
    *,
    offset: int,
    limit: int,
) -> WorkOrderListResponse:
    total = session.exec(select(func.count()).select_from(WorkOrder)).one()
    work_orders = session.exec(
        select(WorkOrder)
        .order_by(WorkOrder.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return WorkOrderListResponse(
        items=[build_work_order_public(item) for item in work_orders],
        total=total,
        offset=offset,
        limit=limit,
    )


def auto_progress_after_sales(
    session: Session,
    *,
    now: datetime | None = None,
    limit: int,
) -> AutoProgressAfterSalesResponse:
    deadline = normalize_datetime(now or utc_now())
    merchant_review_escalated: list[UUID] = []
    buyer_return_closed: list[UUID] = []
    merchant_receipt_refunded: list[UUID] = []

    merchant_review_requests = session.exec(
        select(AfterSalesRequest)
        .where(
            AfterSalesRequest.status == AfterSalesStatus.MERCHANT_REVIEW,
            AfterSalesRequest.merchant_review_due_at <= deadline,
        )
        .limit(limit)
    ).all()
    for request in merchant_review_requests:
        ensure_work_order(
            session,
            request,
            "merchant review timeout",
            priority=WorkOrderPriority.HIGH,
        )
        transition(
            session,
            request,
            to_status=AfterSalesStatus.CUSTOMER_SERVICE,
            actor_user_id=None,
            action="after_sales.auto_escalate_merchant_timeout",
            reason="merchant review timeout",
        )
        merchant_review_escalated.append(request.id)

    buyer_return_requests = session.exec(
        select(AfterSalesRequest)
        .where(
            AfterSalesRequest.status == AfterSalesStatus.WAITING_BUYER_RETURN,
            AfterSalesRequest.buyer_return_due_at <= deadline,
        )
        .limit(limit)
    ).all()
    for request in buyer_return_requests:
        request.closed_reason = "buyer return timeout"
        transition(
            session,
            request,
            to_status=AfterSalesStatus.CLOSED,
            actor_user_id=None,
            action="after_sales.auto_close_buyer_timeout",
            reason="buyer return timeout",
        )
        buyer_return_closed.append(request.id)

    merchant_receipt_requests = session.exec(
        select(AfterSalesRequest)
        .where(
            AfterSalesRequest.status == AfterSalesStatus.WAITING_MERCHANT_RECEIPT,
            AfterSalesRequest.merchant_receipt_due_at <= deadline,
        )
        .limit(limit)
    ).all()
    for request in merchant_receipt_requests:
        start_refund(
            session,
            request,
            actor_user_id=None,
            action="after_sales.auto_confirm_receipt",
            reason="merchant receipt timeout",
            simulate_success=True,
            failure_reason=None,
            idempotency_key=f"auto-confirm-receipt-{request.id}",
        )
        merchant_receipt_refunded.append(request.id)

    commit_or_conflict(session, "after-sales auto progress was already processed")
    return AutoProgressAfterSalesResponse(
        merchant_review_escalated=merchant_review_escalated,
        buyer_return_closed=buyer_return_closed,
        merchant_receipt_refunded=merchant_receipt_refunded,
    )


def start_refund(
    session: Session,
    request: AfterSalesRequest,
    *,
    actor_user_id: UUID | None,
    action: str,
    reason: str,
    simulate_success: bool,
    failure_reason: str | None,
    idempotency_key: str,
) -> Refund:
    if request.status != AfterSalesStatus.REFUNDING:
        transition(
            session,
            request,
            to_status=AfterSalesStatus.REFUNDING,
            actor_user_id=actor_user_id,
            action=action,
            reason=reason,
            idempotency_key=idempotency_key,
        )
    payment = latest_successful_payment(session, request.order_id)
    refund = Refund(
        after_sales_id=request.id,
        order_id=request.order_id,
        payment_id=payment.id if payment else None,
        customer_id=request.customer_id,
        merchant_id=request.merchant_id,
        idempotency_key=idempotency_key,
        amount_cents=request.refund_amount_cents,
        provider_refund_no=f"REF-{request.after_sales_no}-{uuid4().hex[:6].upper()}",
    )
    now = utc_now()
    if simulate_success:
        refund.status = RefundStatus.SUCCEEDED
        refund.refunded_at = now
        request.refunded_at = now
        transition(
            session,
            request,
            to_status=AfterSalesStatus.REFUNDED,
            actor_user_id=actor_user_id,
            action="refund.simulated_success",
            reason=reason,
        )
    else:
        refund.status = RefundStatus.FAILED
        refund.failure_reason = failure_reason or "simulated refund channel failure"
        transition(
            session,
            request,
            to_status=AfterSalesStatus.REFUND_FAILED,
            actor_user_id=actor_user_id,
            action="refund.simulated_failed",
            reason=refund.failure_reason,
        )
    refund.updated_at = now
    session.add(refund)
    session.add(request)
    return refund


def transition(
    session: Session,
    request: AfterSalesRequest,
    *,
    to_status: AfterSalesStatus,
    actor_user_id: UUID | None,
    action: str,
    reason: str | None,
    details: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    from_status = request.status
    try:
        assert_transition(from_status, to_status)
    except AfterSalesStateMachineError as exc:
        raise AfterSalesConflictError(str(exc)) from exc
    request.status = to_status
    request.updated_at = utc_now()
    session.add(request)
    add_event(
        session,
        request,
        action=action,
        actor_user_id=actor_user_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        details=details,
        idempotency_key=idempotency_key,
    )


def add_event(
    session: Session,
    request: AfterSalesRequest,
    *,
    action: str,
    actor_user_id: UUID | None,
    from_status: AfterSalesStatus | None,
    to_status: AfterSalesStatus,
    reason: str | None,
    details: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    session.add(
        AfterSalesEvent(
            after_sales_id=request.id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            idempotency_key=idempotency_key,
            reason=reason,
            details=details,
        )
    )


def ensure_work_order(
    session: Session,
    request: AfterSalesRequest,
    reason: str,
    *,
    priority: WorkOrderPriority,
    assigned_admin_id: UUID | None = None,
) -> WorkOrder:
    existing = session.exec(
        select(WorkOrder).where(
            WorkOrder.after_sales_id == request.id,
            WorkOrder.status == WorkOrderStatus.OPEN,
        )
    ).first()
    if existing is not None:
        if assigned_admin_id is not None:
            existing.assigned_admin_id = assigned_admin_id
        existing.priority = priority
        existing.queue = work_order_queue(request)
        existing.evidence_summary = build_work_order_evidence_summary(request)
        existing.internal_notes = merge_text(existing.internal_notes, f"跟进原因：{reason}")
        existing.updated_at = utc_now()
        session.add(existing)
        return existing
    now = utc_now()
    work_order = WorkOrder(
        work_order_no=generate_work_order_no(now),
        after_sales_id=request.id,
        order_id=request.order_id,
        customer_id=request.customer_id,
        merchant_id=request.merchant_id,
        priority=priority,
        reason=reason,
        queue=work_order_queue(request),
        evidence_summary=build_work_order_evidence_summary(request),
        internal_notes=f"初始原因：{reason}",
        assigned_admin_id=assigned_admin_id,
        created_at=now,
        updated_at=now,
    )
    session.add(work_order)
    return work_order


def resolve_work_order(
    session: Session,
    work_order: WorkOrder,
    actor_user_id: UUID,
    resolution: str,
) -> None:
    work_order.status = WorkOrderStatus.RESOLVED
    work_order.assigned_admin_id = actor_user_id
    work_order.resolution = resolution
    work_order.resolved_at = utc_now()
    work_order.updated_at = utc_now()
    session.add(work_order)


def build_after_sales_public(
    session: Session,
    request: AfterSalesRequest,
) -> AfterSalesPublic:
    refunds = session.exec(
        select(Refund).where(Refund.after_sales_id == request.id).order_by(Refund.created_at)
    ).all()
    events = session.exec(
        select(AfterSalesEvent)
        .where(AfterSalesEvent.after_sales_id == request.id)
        .order_by(AfterSalesEvent.created_at)
    ).all()
    work_order = session.exec(
        select(WorkOrder)
        .where(WorkOrder.after_sales_id == request.id)
        .order_by(WorkOrder.created_at.desc())
    ).first()
    return AfterSalesPublic(
        id=request.id,
        after_sales_no=request.after_sales_no,
        customer_id=request.customer_id,
        merchant_id=request.merchant_id,
        order_id=request.order_id,
        order_item_id=request.order_item_id,
        type=request.type,
        status=request.status,
        reason=request.reason,
        description=request.description,
        evidence_urls=decode_evidence(request.evidence_urls),
        quantity=request.quantity,
        refund_amount_cents=request.refund_amount_cents,
        merchant_response_reason=request.merchant_response_reason,
        return_tracking_no=request.return_tracking_no,
        return_carrier=request.return_carrier,
        merchant_review_due_at=request.merchant_review_due_at,
        buyer_return_due_at=request.buyer_return_due_at,
        merchant_receipt_due_at=request.merchant_receipt_due_at,
        refunded_at=request.refunded_at,
        closed_reason=request.closed_reason,
        created_at=request.created_at,
        updated_at=request.updated_at,
        refunds=[
            RefundPublic(
                id=item.id,
                after_sales_id=item.after_sales_id,
                status=item.status,
                amount_cents=item.amount_cents,
                provider_refund_no=item.provider_refund_no,
                failure_reason=item.failure_reason,
                refunded_at=item.refunded_at,
                created_at=item.created_at,
            )
            for item in refunds
        ],
        events=[
            AfterSalesEventPublic(
                action=item.action,
                from_status=item.from_status,
                to_status=item.to_status,
                idempotency_key=item.idempotency_key,
                reason=item.reason,
                created_at=item.created_at,
            )
            for item in events
        ],
        work_order=build_work_order_public(work_order) if work_order else None,
    )


def build_work_order_public(work_order: WorkOrder) -> WorkOrderPublic:
    return WorkOrderPublic(
        id=work_order.id,
        work_order_no=work_order.work_order_no,
        after_sales_id=work_order.after_sales_id,
        order_id=work_order.order_id,
        customer_id=work_order.customer_id,
        merchant_id=work_order.merchant_id,
        status=work_order.status,
        priority=work_order.priority,
        reason=work_order.reason,
        queue=work_order.queue,
        evidence_summary=work_order.evidence_summary,
        internal_notes=work_order.internal_notes,
        assigned_admin_id=work_order.assigned_admin_id,
        resolution=work_order.resolution,
        created_at=work_order.created_at,
        resolved_at=work_order.resolved_at,
    )


def require_after_sales(session: Session, after_sales_id: UUID) -> AfterSalesRequest:
    request = session.get(AfterSalesRequest, after_sales_id)
    if request is None:
        raise AfterSalesNotFoundError("after-sales request not found")
    return request


def require_order(session: Session, order_id: UUID) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise AfterSalesNotFoundError("order not found")
    return order


def require_order_item(session: Session, order_item_id: UUID) -> OrderItem:
    order_item = session.get(OrderItem, order_item_id)
    if order_item is None:
        raise AfterSalesNotFoundError("order item not found")
    return order_item


def require_merchant_scope(request: AfterSalesRequest, merchant_ids: list[UUID]) -> None:
    if not merchant_ids:
        raise AfterSalesPermissionError("merchant scope required")
    if request.merchant_id not in merchant_ids:
        raise AfterSalesPermissionError("after-sales request belongs to another merchant")


def validate_after_sales_order_status(order: Order, after_sales_type: AfterSalesType) -> None:
    if after_sales_type == AfterSalesType.REFUND_ONLY:
        allowed_statuses = {
            OrderStatus.PAID_PENDING_SHIPMENT,
            OrderStatus.SHIPPED_AWAITING_RECEIPT,
            OrderStatus.COMPLETED,
        }
        if order.status not in allowed_statuses:
            raise AfterSalesConflictError("refund-only requires a paid order")
        return

    if order.status not in {
        OrderStatus.SHIPPED_AWAITING_RECEIPT,
        OrderStatus.COMPLETED,
    }:
        raise AfterSalesConflictError(
            "return-refund requires a shipped or completed order"
        )


def has_idempotent_event(
    session: Session,
    request: AfterSalesRequest,
    idempotency_key: str,
    expected_actions: set[str],
) -> bool:
    event = session.exec(
        select(AfterSalesEvent).where(
            AfterSalesEvent.after_sales_id == request.id,
            AfterSalesEvent.idempotency_key == idempotency_key,
        )
    ).first()
    if event is None:
        return False
    if event.action not in expected_actions:
        raise AfterSalesConflictError("idempotency key conflicts with another action")
    return True


def work_order_queue(request: AfterSalesRequest) -> str:
    if request.status == AfterSalesStatus.REFUND_FAILED:
        return "refund_exception"
    if request.status == AfterSalesStatus.MERCHANT_REVIEW:
        return "merchant_timeout_risk"
    return "customer_service_dispute"


def build_work_order_evidence_summary(request: AfterSalesRequest) -> str:
    evidence_count = len(decode_evidence(request.evidence_urls))
    parts = [
        f"用户诉求：{request.reason}",
        f"凭证数量：{evidence_count}",
    ]
    if request.description:
        parts.append(f"用户说明：{request.description[:160]}")
    if request.merchant_response_reason:
        parts.append(f"商家说明：{request.merchant_response_reason[:160]}")
    if request.return_carrier and request.return_tracking_no:
        parts.append(f"退货物流：{request.return_carrier} {request.return_tracking_no}")
    return "；".join(parts)


def has_open_after_sales_for_order_item(session: Session, order_item_id: UUID) -> bool:
    open_statuses = {
        AfterSalesStatus.MERCHANT_REVIEW,
        AfterSalesStatus.REJECTED,
        AfterSalesStatus.WAITING_BUYER_RETURN,
        AfterSalesStatus.WAITING_MERCHANT_RECEIPT,
        AfterSalesStatus.REFUNDING,
        AfterSalesStatus.REFUND_FAILED,
        AfterSalesStatus.CUSTOMER_SERVICE,
    }
    return (
        session.exec(
            select(AfterSalesRequest.id).where(
                AfterSalesRequest.order_item_id == order_item_id,
                col(AfterSalesRequest.status).in_(open_statuses),
            )
        ).first()
        is not None
    )


def latest_successful_payment(session: Session, order_id: UUID) -> Payment | None:
    return session.exec(
        select(Payment)
        .where(Payment.order_id == order_id, Payment.status == PaymentStatus.SUCCEEDED)
        .order_by(Payment.paid_at.desc())
    ).first()


def build_create_signature(payload: AfterSalesCreateRequest) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    data["evidence_urls"] = sorted(data["evidence_urls"])
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def encode_evidence(evidence_urls: list[str]) -> str:
    return json.dumps(evidence_urls[:10], ensure_ascii=False)


def decode_evidence(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded]


def merge_text(existing: str | None, addition: str) -> str:
    if not existing:
        return addition
    return f"{existing}\n\n补充说明：{addition}"


def generate_after_sales_no(now: datetime) -> str:
    return f"AS{now:%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"


def generate_work_order_no(now: datetime) -> str:
    return f"WO{now:%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def commit_or_conflict(session: Session, message: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise AfterSalesConflictError(message) from exc


def flush_or_conflict(session: Session, message: str) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise AfterSalesConflictError(message) from exc
