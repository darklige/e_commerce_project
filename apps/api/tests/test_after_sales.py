from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domains.after_sales.models import (
    AfterSalesEvent,
    AfterSalesRequest,
    AfterSalesStatus,
    Refund,
    RefundStatus,
    WorkOrder,
    WorkOrderStatus,
)
from app.domains.identity.constants import AccountType, Role
from app.domains.identity.models import AuditLog
from app.domains.identity.service import create_user
from app.domains.order.models import Order, OrderStatus


def login(client: TestClient, email: str, password: str, account_type: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "account_type": account_type},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_admin_token(
    client: TestClient,
    session: Session,
    role: Role = Role.ADMIN_CUSTOMER_SERVICE,
) -> str:
    email = f"after-sales-admin-{role}-{uuid4()}@example.com"
    create_user(
        session,
        email=email,
        password="StrongerPass123!",
        display_name="After Sales Admin",
        account_type=AccountType.ADMIN,
        roles=[role],
    )
    return login(client, email, "StrongerPass123!", "admin")


def create_customer_token(client: TestClient, session: Session, suffix: str) -> str:
    email = f"after-sales-buyer-{suffix}-{uuid4()}@example.com"
    create_user(
        session,
        email=email,
        password="StrongerPass123!",
        display_name=f"Buyer {suffix}",
        account_type=AccountType.CUSTOMER,
    )
    return login(client, email, "StrongerPass123!", "customer")


def create_merchant_token(
    client: TestClient,
    session: Session,
    merchant_id: UUID,
    role: Role,
) -> str:
    email = f"after-sales-merchant-{role}-{merchant_id}-{uuid4()}@example.com"
    create_user(
        session,
        email=email,
        password="StrongerPass123!",
        display_name="After Sales Merchant",
        account_type=AccountType.MERCHANT,
        roles=[role],
        merchant_id=merchant_id,
    )
    return login(client, email, "StrongerPass123!", "merchant")


def seed_paid_order(
    client: TestClient,
    session: Session,
    *,
    customer_suffix: str,
    merchant_id: UUID | None = None,
    order_status: OrderStatus = OrderStatus.SHIPPED_AWAITING_RECEIPT,
) -> tuple[str, str, str, UUID]:
    admin_token = create_admin_token(client, session, Role.ADMIN_OPERATOR)
    merchant_id = merchant_id or uuid4()
    product_token = create_merchant_token(
        client,
        session,
        merchant_id,
        Role.MERCHANT_PRODUCT_OPERATOR,
    )
    customer_token = create_customer_token(client, session, customer_suffix)
    slug = uuid4().hex[:8]
    category_response = client.post(
        "/api/v1/admin/categories",
        json={"name": f"售后类目 {slug}", "slug": f"after-sales-{slug}", "sort_order": 10},
        headers=auth_headers(admin_token),
    )
    assert category_response.status_code == 201
    brand_response = client.post(
        "/api/v1/admin/brands",
        json={"name": f"AfterSalesBrand {slug}", "slug": f"after-sales-brand-{slug}"},
        headers=auth_headers(admin_token),
    )
    assert brand_response.status_code == 201
    product_response = client.post(
        "/api/v1/merchant/products",
        json={
            "category_id": category_response.json()["id"],
            "brand_id": brand_response.json()["id"],
            "title": "Northstar X1",
            "subtitle": "M4 after-sales phone",
            "main_image_url": "https://example.com/x1.png",
            "skus": [
                {
                    "sku_code": f"AS-X1-{slug}",
                    "spec_name": "曜石黑 / 256GB",
                    "price_cents": 399900,
                    "initial_stock": 5,
                }
            ],
        },
        headers=auth_headers(product_token),
    )
    assert product_response.status_code == 201
    sku_id = product_response.json()["skus"][0]["id"]
    publish_response = client.post(
        f"/api/v1/merchant/products/{product_response.json()['id']}/publish",
        headers=auth_headers(product_token),
    )
    assert publish_response.status_code == 200
    add_cart_response = client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 1, "selected": True},
        headers=auth_headers(customer_token),
    )
    assert add_cart_response.status_code == 201
    order_response = client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": f"after-sales-order-{slug}",
            "shipping_address": {
                "receiver_name": "张三",
                "receiver_phone": "13800000000",
                "address": "北京市朝阳区测试路 1 号",
            },
        },
        headers=auth_headers(customer_token),
    )
    assert order_response.status_code == 201
    payment_response = client.post(
        f"/api/v1/orders/{order_response.json()['id']}/payments/simulated",
        json={"idempotency_key": f"after-sales-pay-{slug}", "succeed": True},
        headers=auth_headers(customer_token),
    )
    assert payment_response.status_code == 200
    paid_order = payment_response.json()["order"]
    order = session.get(Order, UUID(paid_order["id"]))
    assert order is not None
    order.status = order_status
    order.updated_at = datetime.now(UTC)
    session.add(order)
    session.commit()
    return (
        customer_token,
        paid_order["id"],
        paid_order["items"][0]["id"],
        merchant_id,
    )


def after_sales_payload(
    order_item_id: str,
    *,
    after_sales_type: str = "return_refund",
    idempotency_key: str = "as-key-001",
) -> dict:
    return {
        "order_item_id": order_item_id,
        "type": after_sales_type,
        "quantity": 1,
        "refund_amount_cents": 399900,
        "reason": "商品存在质量问题",
        "description": "开机后屏幕闪烁",
        "evidence_urls": ["https://example.com/evidence-1.png"],
        "idempotency_key": idempotency_key,
    }


def test_return_refund_happy_path(
    client: TestClient,
    session: Session,
) -> None:
    customer_token, _order_id, order_item_id, merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="happy",
    )
    merchant_token = create_merchant_token(
        client,
        session,
        merchant_id,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    create_response = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id),
        headers=auth_headers(customer_token),
    )
    assert create_response.status_code == 201
    after_sales_id = create_response.json()["id"]
    duplicate_response = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id),
        headers=auth_headers(customer_token),
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == after_sales_id

    approve_response = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/approve",
        json={"reason": "同意退货退款", "idempotency_key": "approve-happy-001"},
        headers=auth_headers(merchant_token),
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "waiting_buyer_return"
    duplicate_approve = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/approve",
        json={"reason": "同意退货退款", "idempotency_key": "approve-happy-001"},
        headers=auth_headers(merchant_token),
    )
    assert duplicate_approve.status_code == 200
    assert duplicate_approve.json()["status"] == "waiting_buyer_return"

    shipment_response = client.post(
        f"/api/v1/after-sales/{after_sales_id}/return-shipment",
        json={
            "carrier": "京东快递",
            "tracking_no": "JDVA0000001",
            "idempotency_key": "shipment-happy-001",
        },
        headers=auth_headers(customer_token),
    )
    assert shipment_response.status_code == 200
    assert shipment_response.json()["status"] == "waiting_merchant_receipt"

    receipt_response = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/confirm-receipt",
        json={"reason": "仓库验收通过", "idempotency_key": "receipt-happy-001"},
        headers=auth_headers(merchant_token),
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["status"] == "refunded"
    assert receipt_response.json()["refunds"][0]["status"] == "succeeded"

    refund = session.exec(select(Refund)).first()
    assert refund is not None
    assert refund.status == RefundStatus.SUCCEEDED
    events = session.exec(select(AfterSalesEvent)).all()
    assert [event.to_status for event in events][-1] == AfterSalesStatus.REFUNDED


def test_reject_supplement_escalate_and_admin_decide(
    client: TestClient,
    session: Session,
) -> None:
    customer_token, _order_id, order_item_id, merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="dispute",
    )
    merchant_token = create_merchant_token(
        client,
        session,
        merchant_id,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    admin_token = create_admin_token(client, session, Role.ADMIN_CUSTOMER_SERVICE)
    create_response = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id, idempotency_key="as-dispute-001"),
        headers=auth_headers(customer_token),
    )
    after_sales_id = create_response.json()["id"]

    reject_response = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/reject",
        json={"reason": "凭证不足", "idempotency_key": "reject-dispute-001"},
        headers=auth_headers(merchant_token),
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    supplement_response = client.post(
        f"/api/v1/after-sales/{after_sales_id}/supplements",
        json={
            "description": "补充开箱视频和检测报告",
            "evidence_urls": ["https://example.com/video.mp4"],
            "idempotency_key": "supplement-dispute-001",
        },
        headers=auth_headers(customer_token),
    )
    assert supplement_response.status_code == 200
    assert supplement_response.json()["status"] == "merchant_review"

    second_reject = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/reject",
        json={"reason": "仍不符合规则", "idempotency_key": "reject-dispute-002"},
        headers=auth_headers(merchant_token),
    )
    assert second_reject.status_code == 200
    escalate_response = client.post(
        f"/api/v1/after-sales/{after_sales_id}/escalate",
        json={
            "reason": "商家多次拒绝，申请客服介入",
            "priority": "high",
            "idempotency_key": "escalate-dispute-001",
        },
        headers=auth_headers(customer_token),
    )
    assert escalate_response.status_code == 200
    assert escalate_response.json()["status"] == "customer_service"
    assert escalate_response.json()["work_order"]["status"] == "open"
    assert "凭证数量" in escalate_response.json()["work_order"]["evidence_summary"]

    decide_response = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/decide",
        json={
            "decision": "approve_refund",
            "reason": "客服裁定支持退款",
            "idempotency_key": "decide-dispute-001",
        },
        headers=auth_headers(admin_token),
    )
    assert decide_response.status_code == 200
    assert decide_response.json()["status"] == "refunded"
    work_order = session.exec(select(WorkOrder)).first()
    assert work_order is not None
    assert work_order.status == WorkOrderStatus.RESOLVED
    assert work_order.evidence_summary is not None
    assert "商家说明" in work_order.evidence_summary


def test_refund_failure_and_admin_retry(
    client: TestClient,
    session: Session,
) -> None:
    customer_token, _order_id, order_item_id, merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="retry",
    )
    merchant_token = create_merchant_token(
        client,
        session,
        merchant_id,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    admin_token = create_admin_token(client, session, Role.ADMIN_FINANCE)
    customer_service_token = create_admin_token(client, session, Role.ADMIN_CUSTOMER_SERVICE)
    create_response = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(
            order_item_id,
            after_sales_type="refund_only",
            idempotency_key="as-retry-001",
        ),
        headers=auth_headers(customer_token),
    )
    after_sales_id = create_response.json()["id"]

    failed_refund = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/approve",
        json={
            "reason": "同意仅退款",
            "simulate_refund_success": False,
            "refund_failure_reason": "channel timeout",
            "idempotency_key": "approve-retry-001",
        },
        headers=auth_headers(merchant_token),
    )
    assert failed_refund.status_code == 200
    assert failed_refund.json()["status"] == "refund_failed"
    assert failed_refund.json()["refunds"][0]["status"] == "failed"

    denied_decision = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/decide",
        json={
            "decision": "approve_refund",
            "reason": "财务不能直接裁决售后",
            "idempotency_key": "finance-decide-denied-001",
        },
        headers=auth_headers(admin_token),
    )
    assert denied_decision.status_code == 403
    denied_retry = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/retry-refund",
        json={"reason": "客服不能重试退款", "idempotency_key": "cs-retry-denied-001"},
        headers=auth_headers(customer_service_token),
    )
    assert denied_retry.status_code == 403

    retry_response = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/retry-refund",
        json={"reason": "渠道恢复，人工重试", "idempotency_key": "retry-refund-001"},
        headers=auth_headers(admin_token),
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == "refunded"
    refunds = session.exec(select(Refund).order_by(Refund.created_at)).all()
    assert [item.status for item in refunds] == [RefundStatus.FAILED, RefundStatus.SUCCEEDED]
    duplicate_retry = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/retry-refund",
        json={"reason": "渠道恢复，人工重试", "idempotency_key": "retry-refund-001"},
        headers=auth_headers(admin_token),
    )
    assert duplicate_retry.status_code == 200
    assert len(duplicate_retry.json()["refunds"]) == 2


def test_after_sales_type_requires_matching_order_status(
    client: TestClient,
    session: Session,
) -> None:
    customer_token, _order_id, order_item_id, _merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="status-refund-only",
        order_status=OrderStatus.PAID_PENDING_SHIPMENT,
    )
    refund_only = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(
            order_item_id,
            after_sales_type="refund_only",
            idempotency_key="as-status-refund-only",
        ),
        headers=auth_headers(customer_token),
    )
    assert refund_only.status_code == 201

    customer_token_2, _order_id_2, order_item_id_2, _merchant_id_2 = seed_paid_order(
        client,
        session,
        customer_suffix="status-return-refund",
        order_status=OrderStatus.PAID_PENDING_SHIPMENT,
    )
    return_refund = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(
            order_item_id_2,
            after_sales_type="return_refund",
            idempotency_key="as-status-return-refund",
        ),
        headers=auth_headers(customer_token_2),
    )
    assert return_refund.status_code == 409


def test_auto_progress_timeouts(
    client: TestClient,
    session: Session,
) -> None:
    admin_token = create_admin_token(client, session, Role.ADMIN_CUSTOMER_SERVICE_LEAD)

    customer_token, _order_id, order_item_id, merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="auto-merchant",
    )
    merchant_timeout = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id, idempotency_key="as-auto-merchant"),
        headers=auth_headers(customer_token),
    )
    merchant_timeout_id = UUID(merchant_timeout.json()["id"])
    request = session.get(AfterSalesRequest, merchant_timeout_id)
    assert request is not None
    request.merchant_review_due_at = datetime.now(UTC) - timedelta(minutes=1)
    session.add(request)

    customer_token_2, _order_id_2, order_item_id_2, merchant_id_2 = seed_paid_order(
        client,
        session,
        customer_suffix="auto-buyer",
    )
    merchant_token_2 = create_merchant_token(
        client,
        session,
        merchant_id_2,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    buyer_timeout = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id_2, idempotency_key="as-auto-buyer"),
        headers=auth_headers(customer_token_2),
    )
    buyer_timeout_id = UUID(buyer_timeout.json()["id"])
    client.post(
        f"/api/v1/merchant/after-sales/{buyer_timeout_id}/approve",
        json={"reason": "同意退货退款", "idempotency_key": "approve-auto-buyer-001"},
        headers=auth_headers(merchant_token_2),
    )
    request_2 = session.get(AfterSalesRequest, buyer_timeout_id)
    assert request_2 is not None
    request_2.buyer_return_due_at = datetime.now(UTC) - timedelta(minutes=1)
    session.add(request_2)

    customer_token_3, _order_id_3, order_item_id_3, merchant_id_3 = seed_paid_order(
        client,
        session,
        customer_suffix="auto-receipt",
    )
    merchant_token_3 = create_merchant_token(
        client,
        session,
        merchant_id_3,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    receipt_timeout = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id_3, idempotency_key="as-auto-receipt"),
        headers=auth_headers(customer_token_3),
    )
    receipt_timeout_id = UUID(receipt_timeout.json()["id"])
    client.post(
        f"/api/v1/merchant/after-sales/{receipt_timeout_id}/approve",
        json={"reason": "同意退货退款", "idempotency_key": "approve-auto-receipt-001"},
        headers=auth_headers(merchant_token_3),
    )
    client.post(
        f"/api/v1/after-sales/{receipt_timeout_id}/return-shipment",
        json={
            "carrier": "京东快递",
            "tracking_no": "JDVA0000002",
            "idempotency_key": "shipment-auto-receipt-001",
        },
        headers=auth_headers(customer_token_3),
    )
    request_3 = session.get(AfterSalesRequest, receipt_timeout_id)
    assert request_3 is not None
    request_3.merchant_receipt_due_at = datetime.now(UTC) - timedelta(minutes=1)
    session.add(request_3)
    session.commit()

    response = client.post(
        "/api/v1/admin/after-sales/auto-progress",
        json={"limit": 20},
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert str(merchant_timeout_id) in body["merchant_review_escalated"]
    assert str(buyer_timeout_id) in body["buyer_return_closed"]
    assert str(receipt_timeout_id) in body["merchant_receipt_refunded"]

    session.expire_all()
    assert session.get(AfterSalesRequest, merchant_timeout_id).status == "customer_service"
    assert session.get(AfterSalesRequest, buyer_timeout_id).status == "closed"
    assert session.get(AfterSalesRequest, receipt_timeout_id).status == "refunded"


def test_after_sales_permissions(
    client: TestClient,
    session: Session,
) -> None:
    customer_token, _order_id, order_item_id, merchant_id = seed_paid_order(
        client,
        session,
        customer_suffix="scope",
    )
    other_customer_token = create_customer_token(client, session, "scope-other")
    merchant_token = create_merchant_token(
        client,
        session,
        merchant_id,
        Role.MERCHANT_ORDER_SUPPORT,
    )
    other_merchant_token = create_merchant_token(
        client,
        session,
        uuid4(),
        Role.MERCHANT_ORDER_SUPPORT,
    )
    create_response = client.post(
        "/api/v1/after-sales",
        json=after_sales_payload(order_item_id, idempotency_key="as-scope-001"),
        headers=auth_headers(customer_token),
    )
    after_sales_id = create_response.json()["id"]

    assert (
        client.get(
            f"/api/v1/after-sales/{after_sales_id}",
            headers=auth_headers(other_customer_token),
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/merchant/after-sales/{after_sales_id}",
            headers=auth_headers(merchant_token),
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/merchant/after-sales/{after_sales_id}",
            headers=auth_headers(other_merchant_token),
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/admin/work-orders",
            headers=auth_headers(customer_token),
        ).status_code
        == 403
    )
    audit_logs = session.exec(
        select(AuditLog).where(AuditLog.action == "after_sales.create")
    ).all()
    assert audit_logs
