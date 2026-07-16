from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domains.after_sales.models import AfterSalesRequest, WorkOrder, WorkOrderStatus
from app.domains.identity.constants import AccountType, Role
from app.domains.identity.models import AuditLog
from app.domains.identity.service import create_user


def login(client: TestClient, email: str, password: str, account_type: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "account_type": account_type},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_staff_token(
    client: TestClient,
    session: Session,
    *,
    account_type: AccountType,
    role: Role,
    email_prefix: str,
    merchant_id: UUID | None = None,
) -> str:
    email = f"{email_prefix}-{uuid4()}@example.com"
    create_user(
        session,
        email=email,
        password="StrongerPass123!",
        display_name=email_prefix.replace("-", " ").title(),
        account_type=account_type,
        roles=[role],
        merchant_id=merchant_id,
    )
    return login(client, email, "StrongerPass123!", account_type.value)


def test_m5_customer_to_merchant_to_admin_after_sales_e2e(
    client: TestClient,
    session: Session,
) -> None:
    merchant_id = uuid4()
    admin_catalog_token = create_staff_token(
        client,
        session,
        account_type=AccountType.ADMIN,
        role=Role.ADMIN_OPERATOR,
        email_prefix="m5-admin-catalog",
    )
    admin_service_token = create_staff_token(
        client,
        session,
        account_type=AccountType.ADMIN,
        role=Role.ADMIN_CUSTOMER_SERVICE,
        email_prefix="m5-admin-service",
    )
    merchant_token = create_staff_token(
        client,
        session,
        account_type=AccountType.MERCHANT,
        role=Role.MERCHANT_OWNER,
        email_prefix="m5-merchant-owner",
        merchant_id=merchant_id,
    )

    customer_email = f"m5-customer-{uuid4()}@example.com"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": customer_email,
            "password": "StrongerPass123!",
            "display_name": "M5 Customer",
        },
    )
    assert register_response.status_code == 201
    customer_token = login(client, customer_email, "StrongerPass123!", "customer")

    assert client.get("/api/v1/auth/me", headers=auth_headers(customer_token)).status_code == 200
    assert (
        client.get("/api/v1/auth/admin/me", headers=auth_headers(customer_token)).status_code
        == 403
    )
    assert (
        client.get("/api/v1/auth/merchant/me", headers=auth_headers(customer_token)).status_code
        == 403
    )
    assert (
        client.get("/api/v1/auth/merchant/me", headers=auth_headers(merchant_token)).status_code
        == 200
    )
    assert (
        client.get("/api/v1/auth/admin/me", headers=auth_headers(admin_service_token)).status_code
        == 200
    )

    slug = uuid4().hex[:8]
    category_response = client.post(
        "/api/v1/admin/categories",
        json={"name": f"M5 数码 {slug}", "slug": f"m5-category-{slug}", "sort_order": 10},
        headers=auth_headers(admin_catalog_token),
    )
    assert category_response.status_code == 201
    brand_response = client.post(
        "/api/v1/admin/brands",
        json={"name": f"M5Brand {slug}", "slug": f"m5-brand-{slug}"},
        headers=auth_headers(admin_catalog_token),
    )
    assert brand_response.status_code == 201

    product_response = client.post(
        "/api/v1/merchant/products",
        json={
            "category_id": category_response.json()["id"],
            "brand_id": brand_response.json()["id"],
            "title": "M5 Northstar X1",
            "subtitle": "Hardening launch regression SKU",
            "main_image_url": "https://example.com/m5-x1.png",
            "skus": [
                {
                    "sku_code": f"M5-X1-{slug}",
                    "spec_name": "曜石黑 / 256GB",
                    "price_cents": 399900,
                    "initial_stock": 3,
                }
            ],
        },
        headers=auth_headers(merchant_token),
    )
    assert product_response.status_code == 201
    product = product_response.json()
    sku_id = product["skus"][0]["id"]

    publish_response = client.post(
        f"/api/v1/merchant/products/{product['id']}/publish",
        headers=auth_headers(merchant_token),
    )
    assert publish_response.status_code == 200
    public_products = client.get("/api/v1/products")
    assert public_products.status_code == 200
    assert public_products.json()["total"] == 1
    assert public_products.json()["items"][0]["id"] == product["id"]

    add_cart_response = client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 1, "selected": True},
        headers=auth_headers(customer_token),
    )
    assert add_cart_response.status_code == 201
    assert add_cart_response.json()["selected_total_cents"] == 399900

    preview_response = client.post(
        "/api/v1/checkout/preview",
        json={},
        headers=auth_headers(customer_token),
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["can_submit"] is True
    assert preview_response.json()["groups"][0]["merchant_id"] == str(merchant_id)

    order_response = client.post(
        "/api/v1/orders",
        json={
            "idempotency_key": "m5-order-e2e-001",
            "shipping_address": {
                "receiver_name": "张三",
                "receiver_phone": "13800000000",
                "address": "北京市朝阳区 M5 测试路 1 号",
            },
        },
        headers=auth_headers(customer_token),
    )
    assert order_response.status_code == 201
    order = order_response.json()
    assert order["status"] == "pending_payment"

    payment_response = client.post(
        f"/api/v1/orders/{order['id']}/payments/simulated",
        json={"idempotency_key": "m5-payment-e2e-001", "succeed": True},
        headers=auth_headers(customer_token),
    )
    assert payment_response.status_code == 200
    paid_order = payment_response.json()["order"]
    assert paid_order["status"] == "paid_pending_shipment"

    merchant_order = client.get(
        f"/api/v1/merchant/orders/{paid_order['id']}",
        headers=auth_headers(merchant_token),
    )
    assert merchant_order.status_code == 200
    admin_order = client.get(
        f"/api/v1/admin/orders/{paid_order['id']}",
        headers=auth_headers(admin_catalog_token),
    )
    assert admin_order.status_code == 200

    after_sales_response = client.post(
        "/api/v1/after-sales",
        json={
            "order_item_id": paid_order["items"][0]["id"],
            "type": "refund_only",
            "quantity": 1,
            "refund_amount_cents": 399900,
            "reason": "商品存在质量问题",
            "description": "开机后屏幕闪烁",
            "evidence_urls": ["https://example.com/m5-evidence-1.png"],
            "idempotency_key": "m5-after-sales-e2e-001",
        },
        headers=auth_headers(customer_token),
    )
    assert after_sales_response.status_code == 201
    after_sales_id = after_sales_response.json()["id"]
    assert after_sales_response.json()["status"] == "merchant_review"

    merchant_list = client.get(
        "/api/v1/merchant/after-sales",
        headers=auth_headers(merchant_token),
    )
    assert merchant_list.status_code == 200
    assert merchant_list.json()["total"] == 1

    reject_response = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/reject",
        json={"reason": "凭证不足", "idempotency_key": "m5-merchant-reject-001"},
        headers=auth_headers(merchant_token),
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    supplement_response = client.post(
        f"/api/v1/after-sales/{after_sales_id}/supplements",
        json={
            "description": "补充检测报告和开箱视频",
            "evidence_urls": ["https://example.com/m5-evidence-2.mp4"],
            "idempotency_key": "m5-customer-supplement-001",
        },
        headers=auth_headers(customer_token),
    )
    assert supplement_response.status_code == 200
    assert supplement_response.json()["status"] == "merchant_review"

    second_reject_response = client.post(
        f"/api/v1/merchant/after-sales/{after_sales_id}/reject",
        json={"reason": "仍不符合规则", "idempotency_key": "m5-merchant-reject-002"},
        headers=auth_headers(merchant_token),
    )
    assert second_reject_response.status_code == 200

    escalate_response = client.post(
        f"/api/v1/after-sales/{after_sales_id}/escalate",
        json={
            "reason": "商家拒绝后申请客服介入",
            "priority": "high",
            "idempotency_key": "m5-customer-escalate-001",
        },
        headers=auth_headers(customer_token),
    )
    assert escalate_response.status_code == 200
    assert escalate_response.json()["status"] == "customer_service"
    assert escalate_response.json()["work_order"]["status"] == "open"

    work_orders = client.get(
        "/api/v1/admin/work-orders",
        headers=auth_headers(admin_service_token),
    )
    assert work_orders.status_code == 200
    assert work_orders.json()["total"] == 1

    decide_response = client.post(
        f"/api/v1/admin/after-sales/{after_sales_id}/decide",
        json={
            "decision": "approve_refund",
            "reason": "客服裁定支持退款",
            "idempotency_key": "m5-admin-decide-001",
        },
        headers=auth_headers(admin_service_token),
    )
    assert decide_response.status_code == 200
    assert decide_response.json()["status"] == "refunded"
    assert decide_response.json()["refunds"][0]["status"] == "succeeded"

    after_sales = session.get(AfterSalesRequest, UUID(after_sales_id))
    assert after_sales is not None
    assert after_sales.status == "refunded"
    work_order = session.exec(select(WorkOrder)).one()
    assert work_order.status == WorkOrderStatus.RESOLVED

    actions = {
        item.action
        for item in session.exec(select(AuditLog).order_by(AuditLog.created_at)).all()
    }
    expected_actions = {
        "auth.register",
        "auth.login",
        "catalog.category_create",
        "catalog.brand_create",
        "catalog.product_publish",
        "order.create",
        "after_sales.create",
        "after_sales.merchant_reject",
        "after_sales.customer_supplement",
        "after_sales.customer_escalate",
        "after_sales.admin_decide",
    }
    missing_actions = expected_actions - actions
    assert not missing_actions
