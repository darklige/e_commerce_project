from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.db.session import SessionDep
from app.domains.after_sales.schemas import (
    AdminDecisionRequest,
    AdminRefundRetryRequest,
    AfterSalesCreateRequest,
    AfterSalesListResponse,
    AfterSalesPublic,
    AfterSalesSupplementRequest,
    AutoProgressAfterSalesRequest,
    AutoProgressAfterSalesResponse,
    CustomerCancelAfterSalesRequest,
    CustomerEscalateRequest,
    MerchantReviewRequest,
    ReturnShipmentRequest,
    WorkOrderListResponse,
)
from app.domains.after_sales.service import (
    AfterSalesConflictError,
    AfterSalesNotFoundError,
    AfterSalesPermissionError,
    admin_decide_after_sales,
    auto_progress_after_sales,
    cancel_after_sales,
    create_after_sales_request,
    escalate_after_sales,
    get_admin_after_sales,
    get_customer_after_sales,
    get_merchant_after_sales,
    list_admin_after_sales,
    list_customer_after_sales,
    list_merchant_after_sales,
    list_work_orders,
    merchant_approve_after_sales,
    merchant_confirm_receipt,
    merchant_reject_after_sales,
    retry_refund,
    submit_return_shipment,
    supplement_after_sales,
)
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission
from app.domains.identity.dependencies import AuthContext, require_permissions

router = APIRouter(tags=["after-sales"])

CustomerAfterSalesDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_MANAGE,
            account_types=(AccountType.CUSTOMER,),
        )
    ),
]
MerchantAfterSalesDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_MANAGE,
            account_types=(AccountType.MERCHANT,),
        )
    ),
]
AdminAfterSalesDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_READ,
            account_types=(AccountType.ADMIN,),
        )
    ),
]
AdminAfterSalesDecisionDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_DECIDE,
            account_types=(AccountType.ADMIN,),
        )
    ),
]
AdminAfterSalesRefundDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_REFUND_RETRY,
            account_types=(AccountType.ADMIN,),
        )
    ),
]
AdminAfterSalesJobDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.AFTER_SALES_AUTO_PROGRESS,
            account_types=(AccountType.ADMIN,),
        )
    ),
]


@router.post("/after-sales", status_code=status.HTTP_201_CREATED)
def create_customer_after_sales(
    payload: AfterSalesCreateRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerAfterSalesDep,
) -> AfterSalesPublic:
    try:
        after_sales = create_after_sales_request(session, auth.user.id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.create",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.get("/after-sales")
def read_customer_after_sales_list(
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AfterSalesListResponse:
    return list_customer_after_sales(session, auth.user.id, offset=offset, limit=limit)


@router.get("/after-sales/{after_sales_id}")
def read_customer_after_sales(
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        return get_customer_after_sales(session, auth.user.id, after_sales_id)
    except (AfterSalesNotFoundError, AfterSalesPermissionError) as exc:
        raise to_http_error(exc) from exc


@router.post("/after-sales/{after_sales_id}/supplements")
def supplement_customer_after_sales(
    payload: AfterSalesSupplementRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = supplement_after_sales(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.customer_supplement",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/after-sales/{after_sales_id}/return-shipment")
def create_return_shipment(
    payload: ReturnShipmentRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = submit_return_shipment(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.return_shipment",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/after-sales/{after_sales_id}/escalate")
def escalate_customer_after_sales(
    payload: CustomerEscalateRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = escalate_after_sales(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.customer_escalate",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/after-sales/{after_sales_id}/cancel")
def cancel_customer_after_sales(
    payload: CustomerCancelAfterSalesRequest,
    request: Request,
    session: SessionDep,
    auth: CustomerAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = cancel_after_sales(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.customer_cancel",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.get("/merchant/after-sales")
def read_merchant_after_sales_list(
    session: SessionDep,
    auth: MerchantAfterSalesDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AfterSalesListResponse:
    try:
        return list_merchant_after_sales(session, auth.merchant_ids, offset=offset, limit=limit)
    except AfterSalesPermissionError as exc:
        raise to_http_error(exc) from exc


@router.get("/merchant/after-sales/{after_sales_id}")
def read_merchant_after_sales(
    session: SessionDep,
    auth: MerchantAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        return get_merchant_after_sales(session, auth.merchant_ids, after_sales_id)
    except (AfterSalesNotFoundError, AfterSalesPermissionError) as exc:
        raise to_http_error(exc) from exc


@router.post("/merchant/after-sales/{after_sales_id}/approve")
def approve_merchant_after_sales(
    payload: MerchantReviewRequest,
    request: Request,
    session: SessionDep,
    auth: MerchantAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = merchant_approve_after_sales(
            session,
            auth.merchant_ids,
            auth.user.id,
            after_sales_id,
            payload,
        )
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.merchant_approve",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/merchant/after-sales/{after_sales_id}/reject")
def reject_merchant_after_sales(
    payload: MerchantReviewRequest,
    request: Request,
    session: SessionDep,
    auth: MerchantAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = merchant_reject_after_sales(
            session,
            auth.merchant_ids,
            auth.user.id,
            after_sales_id,
            payload,
        )
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.merchant_reject",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/merchant/after-sales/{after_sales_id}/confirm-receipt")
def confirm_merchant_receipt(
    payload: MerchantReviewRequest,
    request: Request,
    session: SessionDep,
    auth: MerchantAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = merchant_confirm_receipt(
            session,
            auth.merchant_ids,
            auth.user.id,
            after_sales_id,
            payload,
        )
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.merchant_confirm_receipt",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.get("/admin/after-sales")
def read_admin_after_sales_list(
    session: SessionDep,
    _auth: AdminAfterSalesDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AfterSalesListResponse:
    return list_admin_after_sales(session, offset=offset, limit=limit)


@router.get("/admin/after-sales/{after_sales_id}")
def read_admin_after_sales(
    session: SessionDep,
    _auth: AdminAfterSalesDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        return get_admin_after_sales(session, after_sales_id)
    except AfterSalesNotFoundError as exc:
        raise to_http_error(exc) from exc


@router.post("/admin/after-sales/{after_sales_id}/decide")
def decide_admin_after_sales(
    payload: AdminDecisionRequest,
    request: Request,
    session: SessionDep,
    auth: AdminAfterSalesDecisionDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = admin_decide_after_sales(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.admin_decide",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/admin/after-sales/{after_sales_id}/retry-refund")
def retry_admin_refund(
    payload: AdminRefundRetryRequest,
    request: Request,
    session: SessionDep,
    auth: AdminAfterSalesRefundDep,
    after_sales_id: UUID,
) -> AfterSalesPublic:
    try:
        after_sales = retry_refund(session, auth.user.id, after_sales_id, payload)
    except (
        AfterSalesConflictError,
        AfterSalesNotFoundError,
        AfterSalesPermissionError,
    ) as exc:
        raise to_http_error(exc) from exc
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.admin_retry_refund",
        after_sales.id,
        payload.model_dump(),
    )
    return after_sales


@router.post("/admin/after-sales/auto-progress")
def auto_progress_admin_after_sales(
    payload: AutoProgressAfterSalesRequest,
    request: Request,
    session: SessionDep,
    auth: AdminAfterSalesJobDep,
) -> AutoProgressAfterSalesResponse:
    result = auto_progress_after_sales(session, now=payload.now, limit=payload.limit)
    audit_after_sales_action(
        session,
        request,
        auth,
        "after_sales.auto_progress",
        auth.user.id,
        result.model_dump(),
    )
    return result


@router.get("/admin/work-orders")
def read_admin_work_orders(
    session: SessionDep,
    _auth: AdminAfterSalesDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkOrderListResponse:
    return list_work_orders(session, offset=offset, limit=limit)


def to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AfterSalesNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AfterSalesPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, AfterSalesConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def audit_after_sales_action(
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
        resource_type="after_sales",
        resource_id=str(resource_id),
        outcome="success",
        actor_user_id=auth.user.id,
        details=str(details),
    )
    session.commit()
