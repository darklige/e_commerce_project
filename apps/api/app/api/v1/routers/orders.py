from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.db.session import SessionDep
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission
from app.domains.identity.dependencies import AuthContext, require_permissions
from app.domains.order.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CheckoutPreviewRequest,
    CheckoutPreviewResponse,
    ExpireOrdersRequest,
    ExpireOrdersResponse,
    OrderCancelRequest,
    OrderCreateRequest,
    OrderListResponse,
    OrderPublic,
    PaymentPublic,
    SimulatedPaymentRequest,
)
from app.domains.order.service import (
    CheckoutBlockedError,
    OrderConflictError,
    OrderNotFoundError,
    OrderPermissionError,
    add_cart_item,
    cancel_customer_order,
    create_order_from_cart,
    expire_unpaid_orders,
    get_admin_order,
    get_cart,
    get_customer_order,
    get_merchant_order,
    list_admin_orders,
    list_customer_orders,
    list_merchant_orders,
    preview_checkout,
    remove_cart_item,
    simulate_payment,
    update_cart_item,
)

router = APIRouter(tags=["orders"])

CustomerCartDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.CART_MANAGE,
            account_types=(AccountType.CUSTOMER,),
        )
    ),
]
CustomerOrderDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.ORDER_MANAGE,
            account_types=(AccountType.CUSTOMER,),
        )
    ),
]
MerchantOrderDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.ORDER_MANAGE,
            account_types=(AccountType.MERCHANT,),
        )
    ),
]
AdminOrderDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.ORDER_MANAGE,
            account_types=(AccountType.ADMIN,),
        )
    ),
]


@router.get("/cart")
def read_cart(session: SessionDep, auth: CustomerCartDep) -> CartResponse:
    return get_cart(session, auth.user.id)


@router.post("/cart/items", status_code=status.HTTP_201_CREATED)
def create_cart_item(
    payload: CartItemCreate,
    request: Request,
    session: SessionDep,
    auth: CustomerCartDep,
) -> CartResponse:
    try:
        cart = add_cart_item(session, auth.user.id, payload)
    except (OrderNotFoundError, OrderConflictError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(session, request, auth, "cart.item_add", auth.user.id, payload.model_dump())
    return cart


@router.patch("/cart/items/{cart_item_id}")
def patch_cart_item(
    payload: CartItemUpdate,
    request: Request,
    session: SessionDep,
    auth: CustomerCartDep,
    cart_item_id: UUID,
) -> CartResponse:
    try:
        cart = update_cart_item(session, auth.user.id, cart_item_id, payload)
    except (OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(
        session,
        request,
        auth,
        "cart.item_update",
        cart_item_id,
        payload.model_dump(),
    )
    return cart


@router.delete("/cart/items/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(
    request: Request,
    session: SessionDep,
    auth: CustomerCartDep,
    cart_item_id: UUID,
) -> Response:
    try:
        remove_cart_item(session, auth.user.id, cart_item_id)
    except (OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(session, request, auth, "cart.item_remove", cart_item_id, {})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/checkout/preview")
def create_checkout_preview(
    payload: CheckoutPreviewRequest,
    session: SessionDep,
    auth: CustomerOrderDep,
) -> CheckoutPreviewResponse:
    return preview_checkout(session, auth.user.id, payload)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_customer_order(
    payload: OrderCreateRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerOrderDep,
) -> OrderPublic:
    try:
        order = create_order_from_cart(session, auth.user.id, payload)
    except (CheckoutBlockedError, OrderConflictError, OrderNotFoundError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(session, request, auth, "order.create", order.id, payload.model_dump())
    return order


@router.get("/orders")
def read_customer_orders(
    session: SessionDep,
    auth: CustomerOrderDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderListResponse:
    return list_customer_orders(session, auth.user.id, offset=offset, limit=limit)


@router.get("/orders/{order_id}")
def read_customer_order(
    session: SessionDep,
    auth: CustomerOrderDep,
    order_id: UUID,
) -> OrderPublic:
    try:
        return get_customer_order(session, auth.user.id, order_id)
    except (OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    payload: OrderCancelRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerOrderDep,
    order_id: UUID,
) -> OrderPublic:
    try:
        order = cancel_customer_order(session, auth.user.id, order_id, payload)
    except (OrderConflictError, OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(session, request, auth, "order.cancel", order.id, payload.model_dump())
    return order


@router.post("/orders/{order_id}/payments/simulated")
def create_simulated_payment(
    payload: SimulatedPaymentRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerOrderDep,
    order_id: UUID,
) -> PaymentPublic:
    try:
        payment = simulate_payment(session, auth.user.id, order_id, payload)
    except (OrderConflictError, OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc
    audit_order_action(
        session,
        request,
        auth,
        "payment.simulated",
        payment.order_id,
        payload.model_dump(),
    )
    return payment


@router.get("/merchant/orders")
def read_merchant_orders(
    session: SessionDep,
    auth: MerchantOrderDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderListResponse:
    try:
        return list_merchant_orders(session, auth.merchant_ids, offset=offset, limit=limit)
    except OrderPermissionError as exc:
        raise to_http_error(exc) from exc


@router.get("/merchant/orders/{order_id}")
def read_merchant_order(
    session: SessionDep,
    auth: MerchantOrderDep,
    order_id: UUID,
) -> OrderPublic:
    try:
        return get_merchant_order(session, auth.merchant_ids, order_id)
    except (OrderNotFoundError, OrderPermissionError) as exc:
        raise to_http_error(exc) from exc


@router.get("/admin/orders")
def read_admin_orders(
    session: SessionDep,
    _auth: AdminOrderDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderListResponse:
    return list_admin_orders(session, offset=offset, limit=limit)


@router.get("/admin/orders/{order_id}")
def read_admin_order(
    session: SessionDep,
    _auth: AdminOrderDep,
    order_id: UUID,
) -> OrderPublic:
    try:
        return get_admin_order(session, order_id)
    except OrderNotFoundError as exc:
        raise to_http_error(exc) from exc


@router.post("/admin/orders/expire-unpaid")
def expire_pending_orders(
    payload: ExpireOrdersRequest,
    request: Request,
    session: SessionDep,
    auth: AdminOrderDep,
) -> ExpireOrdersResponse:
    expired_order_ids = expire_unpaid_orders(session, now=payload.now, limit=payload.limit)
    audit_order_action(
        session,
        request,
        auth,
        "order.expire_unpaid",
        auth.user.id,
        {"count": len(expired_order_ids)},
    )
    return ExpireOrdersResponse(expired_order_ids=expired_order_ids, count=len(expired_order_ids))


def to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, OrderNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, OrderPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, CheckoutBlockedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "checkout blocked", "blockers": exc.blockers},
        )
    if isinstance(exc, OrderConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def audit_order_action(
    session: SessionDep,
    request: Request,
    auth: AuthContext,
    action: str,
    resource_id: UUID,
    details: dict,
) -> None:
    write_audit_log(
        session,
        request=request,
        action=action,
        resource_type="order",
        resource_id=str(resource_id),
        outcome="success",
        actor_user_id=auth.user.id,
        details=str(details),
    )
    session.commit()
