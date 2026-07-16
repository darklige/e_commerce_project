import hashlib
import json
from collections import defaultdict
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, delete, select

from app.domains.catalog.models import Product, ProductStatus, Sku, SkuInventory
from app.domains.catalog.schemas import InventoryReservationRequest
from app.domains.catalog.service import (
    CatalogConflictError,
    CatalogNotFoundError,
    InventoryInsufficientError,
    consume_inventory_reservation,
    release_inventory_reservation,
    reserve_inventory,
)
from app.domains.order.models import (
    CartItem,
    Order,
    OrderCloseReason,
    OrderItem,
    OrderStatus,
    OrderStatusEvent,
    Payment,
    PaymentProvider,
    PaymentStatus,
    utc_now,
)
from app.domains.order.schemas import (
    CartItemCreate,
    CartItemPublic,
    CartItemUpdate,
    CartResponse,
    CheckoutMerchantGroup,
    CheckoutPreviewRequest,
    CheckoutPreviewResponse,
    OrderCancelRequest,
    OrderCreateRequest,
    OrderItemPublic,
    OrderListResponse,
    OrderPublic,
    OrderTimelineEvent,
    PaymentPublic,
    SimulatedPaymentRequest,
)
from app.domains.order.state_machine import OrderStateMachineError, assert_transition

DEFAULT_SHIPPING_FEE_CENTS = 0


class OrderError(Exception):
    pass


class OrderNotFoundError(OrderError):
    pass


class OrderPermissionError(OrderError):
    pass


class OrderConflictError(OrderError):
    pass


class CheckoutBlockedError(OrderError):
    def __init__(self, blockers: list[str]) -> None:
        self.blockers = blockers
        super().__init__("; ".join(blockers))


def get_cart(session: Session, customer_id: UUID) -> CartResponse:
    cart_items = list_customer_cart_items(session, customer_id)
    return build_cart_response(session, cart_items)


def add_cart_item(session: Session, customer_id: UUID, payload: CartItemCreate) -> CartResponse:
    require_purchasable_sku(session, payload.sku_id)
    existing = session.exec(
        select(CartItem).where(
            CartItem.customer_id == customer_id,
            CartItem.sku_id == payload.sku_id,
        )
    ).first()
    if existing is None:
        session.add(
            CartItem(
                customer_id=customer_id,
                sku_id=payload.sku_id,
                quantity=payload.quantity,
                selected=payload.selected,
            )
        )
    else:
        existing.quantity = min(existing.quantity + payload.quantity, 100)
        existing.selected = payload.selected
        existing.updated_at = utc_now()
        session.add(existing)
    commit_or_conflict(session, "cart item already exists")
    return get_cart(session, customer_id)


def update_cart_item(
    session: Session,
    customer_id: UUID,
    cart_item_id: UUID,
    payload: CartItemUpdate,
) -> CartResponse:
    cart_item = require_cart_item(session, customer_id, cart_item_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(cart_item, field_name, value)
    cart_item.updated_at = utc_now()
    session.add(cart_item)
    session.commit()
    return get_cart(session, customer_id)


def remove_cart_item(session: Session, customer_id: UUID, cart_item_id: UUID) -> None:
    cart_item = require_cart_item(session, customer_id, cart_item_id)
    session.delete(cart_item)
    session.commit()


def preview_checkout(
    session: Session,
    customer_id: UUID,
    payload: CheckoutPreviewRequest,
) -> CheckoutPreviewResponse:
    cart_items = select_checkout_cart_items(session, customer_id, payload.cart_item_ids)
    return build_checkout_preview(session, cart_items)


def create_order_from_cart(
    session: Session,
    customer_id: UUID,
    payload: OrderCreateRequest,
) -> OrderPublic:
    request_signature = build_order_request_signature(payload)
    existing = session.exec(
        select(Order).where(
            Order.customer_id == customer_id,
            Order.idempotency_key == payload.idempotency_key,
        )
    ).first()
    if existing is not None:
        if existing.request_signature != request_signature:
            raise OrderConflictError("idempotency key conflicts with another order request")
        return build_order_public(session, existing)

    cart_items = select_checkout_cart_items(session, customer_id, payload.cart_item_ids)
    preview = build_checkout_preview(session, cart_items)
    if not preview.can_submit:
        raise CheckoutBlockedError(preview.blockers)

    now = utc_now()
    order = Order(
        order_no=generate_order_no(now),
        customer_id=customer_id,
        idempotency_key=payload.idempotency_key,
        request_signature=request_signature,
        items_total_cents=preview.items_total_cents,
        shipping_fee_cents=preview.shipping_fee_cents,
        payable_total_cents=preview.payable_total_cents,
        receiver_name=payload.shipping_address.receiver_name,
        receiver_phone=payload.shipping_address.receiver_phone,
        shipping_address=payload.shipping_address.address,
        created_at=now,
        updated_at=now,
    )
    session.add(order)
    flush_or_conflict(session, "order idempotency key already exists")

    public_items_by_cart_id = {
        item.id: build_cart_item_public(session, item) for item in cart_items
    }
    for cart_item in cart_items:
        public_item = public_items_by_cart_id[cart_item.id]
        reservation, _available = reserve_inventory(
            session,
            public_item.merchant_id,
            InventoryReservationRequest(
                sku_id=cart_item.sku_id,
                quantity=cart_item.quantity,
                idempotency_key=f"order:{order.id}:{cart_item.id}",
            ),
            commit=False,
        )
        session.add(
            OrderItem(
                order_id=order.id,
                customer_id=customer_id,
                merchant_id=public_item.merchant_id,
                product_id=public_item.product_id,
                sku_id=public_item.sku_id,
                reservation_id=reservation.id,
                product_title=public_item.title,
                sku_spec_name=public_item.sku_spec_name,
                sku_code=require_sku(session, public_item.sku_id).sku_code,
                product_image_url=public_item.main_image_url,
                unit_price_cents=public_item.unit_price_cents,
                quantity=public_item.quantity,
                line_total_cents=public_item.line_total_cents,
            )
        )

    session.exec(delete(CartItem).where(col(CartItem.id).in_([item.id for item in cart_items])))
    add_order_event(
        session,
        order,
        action="order.create",
        from_status=None,
        to_status=OrderStatus.PENDING_PAYMENT,
        actor_user_id=customer_id,
        reason="customer checkout",
    )
    commit_or_conflict(session, "order already exists")
    session.refresh(order)
    return build_order_public(session, order)


def list_customer_orders(
    session: Session,
    customer_id: UUID,
    *,
    offset: int,
    limit: int,
) -> OrderListResponse:
    total = session.exec(
        select(func.count()).select_from(Order).where(Order.customer_id == customer_id)
    ).one()
    orders = session.exec(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return OrderListResponse(
        items=[build_order_public(session, order) for order in orders],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_customer_order(session: Session, customer_id: UUID, order_id: UUID) -> OrderPublic:
    order = require_order(session, order_id)
    if order.customer_id != customer_id:
        raise OrderPermissionError("order belongs to another customer")
    return build_order_public(session, order)


def cancel_customer_order(
    session: Session,
    customer_id: UUID,
    order_id: UUID,
    payload: OrderCancelRequest,
) -> OrderPublic:
    order = require_order(session, order_id)
    if order.customer_id != customer_id:
        raise OrderPermissionError("order belongs to another customer")
    if order.status == OrderStatus.CLOSED:
        return build_order_public(session, order)
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise OrderConflictError("only pending payment orders can be cancelled by customer")
    close_order(
        session,
        order,
        actor_user_id=customer_id,
        action="order.cancel",
        reason=OrderCloseReason.CUSTOMER_CANCELLED,
        note=payload.reason,
    )
    session.commit()
    session.refresh(order)
    return build_order_public(session, order)


def simulate_payment(
    session: Session,
    customer_id: UUID,
    order_id: UUID,
    payload: SimulatedPaymentRequest,
) -> PaymentPublic:
    order = require_order(session, order_id)
    if order.customer_id != customer_id:
        raise OrderPermissionError("order belongs to another customer")

    existing = session.exec(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.idempotency_key == payload.idempotency_key,
        )
    ).first()
    if existing is not None:
        return build_payment_public(session, existing)

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise OrderConflictError("only pending payment orders can be paid")
    if is_at_or_before(order.expires_at, utc_now()):
        close_order(
            session,
            order,
            actor_user_id=None,
            action="order.expire",
            reason=OrderCloseReason.PAYMENT_TIMEOUT,
            note="payment window expired before simulated payment",
        )
        session.commit()
        raise OrderConflictError("order payment window has expired")

    now = utc_now()
    payment = Payment(
        order_id=order.id,
        customer_id=customer_id,
        idempotency_key=payload.idempotency_key,
        amount_cents=order.payable_total_cents,
        provider=PaymentProvider.SIMULATED,
        provider_trade_no=f"SIM-{order.order_no}-{payload.idempotency_key[:8]}",
    )
    session.add(payment)
    flush_or_conflict(session, "payment idempotency key already exists")

    if payload.succeed:
        transition_order(
            session,
            order,
            to_status=OrderStatus.PAID_PENDING_SHIPMENT,
            actor_user_id=customer_id,
            action="payment.simulated_success",
            reason="simulated payment succeeded",
        )
        for item in list_order_items(session, order.id):
            consume_inventory_reservation(session, item.reservation_id, commit=False)
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = now
        order.paid_at = now
        order.updated_at = now
    else:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = payload.failure_reason or "simulated payment failed"
        close_order(
            session,
            order,
            actor_user_id=customer_id,
            action="payment.simulated_failed",
            reason=OrderCloseReason.PAYMENT_FAILED,
            note=payment.failure_reason,
        )

    payment.updated_at = now
    session.add(payment)
    session.add(order)
    session.commit()
    session.refresh(payment)
    return build_payment_public(session, payment)


def expire_unpaid_orders(
    session: Session,
    *,
    now: datetime | None = None,
    limit: int = 50,
) -> list[UUID]:
    deadline = now or utc_now()
    orders = session.exec(
        select(Order)
        .where(
            Order.status == OrderStatus.PENDING_PAYMENT,
            Order.expires_at <= deadline,
        )
        .order_by(Order.expires_at)
        .limit(limit)
    ).all()
    expired_ids: list[UUID] = []
    for order in orders:
        close_order(
            session,
            order,
            actor_user_id=None,
            action="order.expire",
            reason=OrderCloseReason.PAYMENT_TIMEOUT,
            note="payment timeout",
        )
        expired_ids.append(order.id)
    session.commit()
    return expired_ids


def list_merchant_orders(
    session: Session,
    merchant_ids: list[UUID],
    *,
    offset: int,
    limit: int,
) -> OrderListResponse:
    if not merchant_ids:
        raise OrderPermissionError("merchant scope required")
    total = session.exec(
        select(func.count(func.distinct(Order.id)))
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(col(OrderItem.merchant_id).in_(merchant_ids))
    ).one()
    orders = session.exec(
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(col(OrderItem.merchant_id).in_(merchant_ids))
        .distinct()
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return OrderListResponse(
        items=[build_order_public(session, order, merchant_ids=merchant_ids) for order in orders],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_merchant_order(
    session: Session,
    merchant_ids: list[UUID],
    order_id: UUID,
) -> OrderPublic:
    order = require_order(session, order_id)
    if not merchant_ids:
        raise OrderPermissionError("merchant scope required")
    if not has_merchant_order_scope(session, order.id, merchant_ids):
        raise OrderPermissionError("order belongs to another merchant")
    return build_order_public(session, order, merchant_ids=merchant_ids)


def list_admin_orders(session: Session, *, offset: int, limit: int) -> OrderListResponse:
    total = session.exec(select(func.count()).select_from(Order)).one()
    orders = session.exec(
        select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return OrderListResponse(
        items=[build_order_public(session, order) for order in orders],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_admin_order(session: Session, order_id: UUID) -> OrderPublic:
    return build_order_public(session, require_order(session, order_id))


def build_checkout_preview(
    session: Session,
    cart_items: list[CartItem],
) -> CheckoutPreviewResponse:
    blockers: list[str] = []
    public_items = [build_cart_item_public(session, item) for item in cart_items]
    for item in public_items:
        if item.warning is not None:
            blockers.append(f"{item.title} {item.sku_spec_name}: {item.warning}")
    if not public_items:
        blockers.append("checkout requires at least one selected cart item")

    groups_map: dict[UUID, list[CartItemPublic]] = defaultdict(list)
    for item in public_items:
        groups_map[item.merchant_id].append(item)

    groups = [
        CheckoutMerchantGroup(
            merchant_id=merchant_id,
            items=items,
            subtotal_cents=sum(item.line_total_cents for item in items),
        )
        for merchant_id, items in sorted(groups_map.items(), key=lambda pair: str(pair[0]))
    ]
    items_total_cents = sum(group.subtotal_cents for group in groups)
    shipping_fee_cents = DEFAULT_SHIPPING_FEE_CENTS if public_items else 0
    return CheckoutPreviewResponse(
        groups=groups,
        items_total_cents=items_total_cents,
        shipping_fee_cents=shipping_fee_cents,
        payable_total_cents=items_total_cents + shipping_fee_cents,
        can_submit=not blockers,
        blockers=blockers,
    )


def build_cart_response(session: Session, cart_items: list[CartItem]) -> CartResponse:
    public_items = [build_cart_item_public(session, item) for item in cart_items]
    selected_items = [item for item in public_items if item.selected]
    return CartResponse(
        items=public_items,
        selected_count=sum(item.quantity for item in selected_items),
        selected_total_cents=sum(item.line_total_cents for item in selected_items),
    )


def build_cart_item_public(session: Session, cart_item: CartItem) -> CartItemPublic:
    sku = require_sku(session, cart_item.sku_id)
    product = require_product(session, sku.spu_id)
    inventory = require_inventory(session, sku.id)
    available = inventory.on_hand - inventory.reserved
    warning = None
    if product.status != ProductStatus.PUBLISHED:
        warning = "product is not available"
    elif not sku.is_active:
        warning = "sku is not available"
    elif available <= 0:
        warning = "out of stock"
    elif cart_item.quantity > available:
        warning = f"only {available} available"

    return CartItemPublic(
        id=cart_item.id,
        sku_id=sku.id,
        product_id=product.id,
        merchant_id=sku.merchant_id,
        title=product.title,
        subtitle=product.subtitle,
        sku_spec_name=sku.spec_name,
        main_image_url=product.main_image_url,
        unit_price_cents=sku.price_cents,
        quantity=cart_item.quantity,
        selected=cart_item.selected,
        available=max(available, 0),
        line_total_cents=sku.price_cents * cart_item.quantity,
        warning=warning,
    )


def build_order_public(
    session: Session,
    order: Order,
    *,
    merchant_ids: list[UUID] | None = None,
) -> OrderPublic:
    items = list_order_items(session, order.id)
    if merchant_ids is not None:
        items = [item for item in items if item.merchant_id in merchant_ids]
    events = session.exec(
        select(OrderStatusEvent)
        .where(OrderStatusEvent.order_id == order.id)
        .order_by(OrderStatusEvent.created_at)
    ).all()
    return OrderPublic(
        id=order.id,
        order_no=order.order_no,
        customer_id=order.customer_id,
        status=order.status,
        items_total_cents=order.items_total_cents,
        shipping_fee_cents=order.shipping_fee_cents,
        payable_total_cents=order.payable_total_cents,
        currency=order.currency,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        shipping_address=order.shipping_address,
        close_reason=order.close_reason,
        close_note=order.close_note,
        paid_at=order.paid_at,
        expires_at=order.expires_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemPublic(
                id=item.id,
                merchant_id=item.merchant_id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                product_title=item.product_title,
                sku_spec_name=item.sku_spec_name,
                sku_code=item.sku_code,
                product_image_url=item.product_image_url,
                unit_price_cents=item.unit_price_cents,
                quantity=item.quantity,
                line_total_cents=item.line_total_cents,
            )
            for item in items
        ],
        timeline=[
            OrderTimelineEvent(
                action=event.action,
                from_status=event.from_status,
                to_status=event.to_status,
                reason=event.reason,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


def build_payment_public(session: Session, payment: Payment) -> PaymentPublic:
    order = require_order(session, payment.order_id)
    return PaymentPublic(
        id=payment.id,
        order_id=payment.order_id,
        status=payment.status,
        amount_cents=payment.amount_cents,
        provider_trade_no=payment.provider_trade_no,
        paid_at=payment.paid_at,
        order=build_order_public(session, order),
    )


def close_order(
    session: Session,
    order: Order,
    *,
    actor_user_id: UUID | None,
    action: str,
    reason: OrderCloseReason,
    note: str,
) -> None:
    if order.status == OrderStatus.CLOSED:
        return
    transition_order(
        session,
        order,
        to_status=OrderStatus.CLOSED,
        actor_user_id=actor_user_id,
        action=action,
        reason=reason,
        details=note,
    )
    for item in list_order_items(session, order.id):
        release_inventory_reservation(session, item.reservation_id, commit=False)
    order.close_reason = reason
    order.close_note = note
    order.updated_at = utc_now()
    session.add(order)


def transition_order(
    session: Session,
    order: Order,
    *,
    to_status: OrderStatus,
    actor_user_id: UUID | None,
    action: str,
    reason: str | OrderCloseReason | None,
    details: str | None = None,
) -> None:
    from_status = order.status
    try:
        assert_transition(from_status, to_status)
    except OrderStateMachineError as exc:
        raise OrderConflictError(str(exc)) from exc
    order.status = to_status
    order.updated_at = utc_now()
    session.add(order)
    add_order_event(
        session,
        order,
        action=action,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor_user_id,
        reason=str(reason) if reason is not None else None,
        details=details,
    )


def add_order_event(
    session: Session,
    order: Order,
    *,
    action: str,
    from_status: OrderStatus | None,
    to_status: OrderStatus,
    actor_user_id: UUID | None,
    reason: str | None = None,
    details: str | None = None,
) -> None:
    session.add(
        OrderStatusEvent(
            order_id=order.id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            reason=reason,
            details=details,
        )
    )


def list_customer_cart_items(session: Session, customer_id: UUID) -> list[CartItem]:
    return list(
        session.exec(
            select(CartItem)
            .where(CartItem.customer_id == customer_id)
            .order_by(CartItem.updated_at.desc())
        ).all()
    )


def select_checkout_cart_items(
    session: Session,
    customer_id: UUID,
    cart_item_ids: list[UUID] | None,
) -> list[CartItem]:
    statement = select(CartItem).where(CartItem.customer_id == customer_id)
    if cart_item_ids is None:
        statement = statement.where(CartItem.selected == True)  # noqa: E712
    else:
        if not cart_item_ids:
            return []
        statement = statement.where(col(CartItem.id).in_(cart_item_ids))
    return list(session.exec(statement.order_by(CartItem.created_at)).all())


def require_cart_item(session: Session, customer_id: UUID, cart_item_id: UUID) -> CartItem:
    item = session.get(CartItem, cart_item_id)
    if item is None:
        raise OrderNotFoundError("cart item not found")
    if item.customer_id != customer_id:
        raise OrderPermissionError("cart item belongs to another customer")
    return item


def require_purchasable_sku(session: Session, sku_id: UUID) -> Sku:
    sku = require_sku(session, sku_id)
    product = require_product(session, sku.spu_id)
    if product.status != ProductStatus.PUBLISHED or not sku.is_active:
        raise OrderConflictError("sku is not available for purchase")
    return sku


def require_sku(session: Session, sku_id: UUID) -> Sku:
    sku = session.get(Sku, sku_id)
    if sku is None:
        raise OrderNotFoundError("sku not found")
    return sku


def require_product(session: Session, product_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise OrderNotFoundError("product not found")
    return product


def require_inventory(session: Session, sku_id: UUID) -> SkuInventory:
    inventory = session.get(SkuInventory, sku_id)
    if inventory is None:
        raise OrderNotFoundError("inventory not found")
    return inventory


def require_order(session: Session, order_id: UUID) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise OrderNotFoundError("order not found")
    return order


def list_order_items(session: Session, order_id: UUID) -> list[OrderItem]:
    return list(
        session.exec(
            select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.created_at)
        ).all()
    )


def has_merchant_order_scope(session: Session, order_id: UUID, merchant_ids: list[UUID]) -> bool:
    return (
        session.exec(
            select(OrderItem.id).where(
                OrderItem.order_id == order_id,
                col(OrderItem.merchant_id).in_(merchant_ids),
            )
        ).first()
        is not None
    )


def is_at_or_before(left: datetime, right: datetime) -> bool:
    if left.tzinfo is None and right.tzinfo is not None:
        right = right.replace(tzinfo=None)
    if left.tzinfo is not None and right.tzinfo is None:
        left = left.replace(tzinfo=None)
    return left <= right


def build_order_request_signature(payload: OrderCreateRequest) -> str:
    data = payload.model_dump(mode="json", exclude={"idempotency_key"})
    if data.get("cart_item_ids") is not None:
        data["cart_item_ids"] = sorted(data["cart_item_ids"])
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def generate_order_no(now: datetime) -> str:
    return f"JD{now:%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"


def commit_or_conflict(session: Session, message: str) -> None:
    try:
        session.commit()
    except (
        IntegrityError,
        CatalogConflictError,
        CatalogNotFoundError,
        InventoryInsufficientError,
    ) as exc:
        session.rollback()
        raise OrderConflictError(message if isinstance(exc, IntegrityError) else str(exc)) from exc


def flush_or_conflict(session: Session, message: str) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise OrderConflictError(message) from exc
