from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domains.catalog.models import InventoryReservation, ReservationStatus, SkuInventory
from app.domains.identity.constants import AccountType, Role
from app.domains.identity.models import AuditLog
from app.domains.identity.service import create_user
from app.domains.order.models import CartItem, Order, OrderStatus, Payment


def login(client: TestClient, email: str, password: str, account_type: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "account_type": account_type},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_admin_token(client: TestClient, session: Session) -> str:
    email = f"orders-admin-{uuid4()}@example.com"
    create_user(
        session,
        email=email,
        password="StrongerPass123!",
        display_name="Orders Admin",
        account_type=AccountType.ADMIN,
        roles=[Role.ADMIN_OPERATOR],
    )
    return login(client, email, "StrongerPass123!", "admin")


def create_customer_token(client: TestClient, session: Session, suffix: str = "one") -> str:
    create_user(
        session,
        email=f"buyer-m3-{suffix}@example.com",
        password="StrongerPass123!",
        display_name=f"Buyer {suffix}",
        account_type=AccountType.CUSTOMER,
    )
    return login(client, f"buyer-m3-{suffix}@example.com", "StrongerPass123!", "customer")


def create_merchant_token(client: TestClient, session: Session, merchant_id: UUID) -> str:
    create_user(
        session,
        email=f"merchant-m3-{merchant_id}@example.com",
        password="StrongerPass123!",
        display_name="Merchant",
        account_type=AccountType.MERCHANT,
        roles=[Role.MERCHANT_ORDER_SUPPORT],
        merchant_id=merchant_id,
    )
    return login(client, f"merchant-m3-{merchant_id}@example.com", "StrongerPass123!", "merchant")


def create_product_operator_token(
    client: TestClient,
    session: Session,
    merchant_id: UUID,
) -> str:
    create_user(
        session,
        email=f"merchant-product-m3-{merchant_id}@example.com",
        password="StrongerPass123!",
        display_name="Merchant Product",
        account_type=AccountType.MERCHANT,
        roles=[Role.MERCHANT_PRODUCT_OPERATOR],
        merchant_id=merchant_id,
    )
    return login(
        client,
        f"merchant-product-m3-{merchant_id}@example.com",
        "StrongerPass123!",
        "merchant",
    )


def seed_published_product(
    client: TestClient,
    session: Session,
    *,
    merchant_id: UUID | None = None,
    stock: int = 5,
    price_cents: int = 399900,
) -> tuple[str, str, UUID]:
    admin_token = create_admin_token(client, session)
    merchant_id = merchant_id or uuid4()
    merchant_token = create_product_operator_token(client, session, merchant_id)
    slug = uuid4().hex[:8]
    category_response = client.post(
        "/api/v1/admin/categories",
        json={"name": f"订单类目 {slug}", "slug": f"orders-{slug}", "sort_order": 10},
        headers=auth_headers(admin_token),
    )
    assert category_response.status_code == 201
    brand_response = client.post(
        "/api/v1/admin/brands",
        json={"name": f"OrderBrand {slug}", "slug": f"order-brand-{slug}"},
        headers=auth_headers(admin_token),
    )
    assert brand_response.status_code == 201
    product_response = client.post(
        "/api/v1/merchant/products",
        json={
            "category_id": category_response.json()["id"],
            "brand_id": brand_response.json()["id"],
            "title": "Northstar X1",
            "subtitle": "M3 checkout phone",
            "main_image_url": "https://example.com/x1.png",
            "skus": [
                {
                    "sku_code": f"NS-X1-{slug}",
                    "spec_name": "曜石黑 / 256GB",
                    "price_cents": price_cents,
                    "initial_stock": stock,
                }
            ],
        },
        headers=auth_headers(merchant_token),
    )
    assert product_response.status_code == 201
    product = product_response.json()
    publish_response = client.post(
        f"/api/v1/merchant/products/{product['id']}/publish",
        headers=auth_headers(merchant_token),
    )
    assert publish_response.status_code == 200
    return product["id"], product["skus"][0]["id"], merchant_id


def order_request(idempotency_key: str = "order-key-001") -> dict:
    return {
        "idempotency_key": idempotency_key,
        "shipping_address": {
            "receiver_name": "张三",
            "receiver_phone": "13800000000",
            "address": "北京市朝阳区测试路 1 号",
        },
    }


def test_cart_checkout_order_payment_flow_is_idempotent(
    client: TestClient,
    session: Session,
) -> None:
    _product_id, sku_id, merchant_id = seed_published_product(client, session, stock=5)
    customer_token = create_customer_token(client, session)

    add_response = client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 2, "selected": True},
        headers=auth_headers(customer_token),
    )
    assert add_response.status_code == 201
    assert add_response.json()["selected_total_cents"] == 799800

    preview_response = client.post(
        "/api/v1/checkout/preview",
        json={},
        headers=auth_headers(customer_token),
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["can_submit"] is True
    assert preview_response.json()["groups"][0]["merchant_id"] == str(merchant_id)

    first_order = client.post(
        "/api/v1/orders",
        json=order_request(),
        headers=auth_headers(customer_token),
    )
    second_order = client.post(
        "/api/v1/orders",
        json=order_request(),
        headers=auth_headers(customer_token),
    )
    assert first_order.status_code == 201
    assert second_order.status_code == 201
    assert first_order.json()["id"] == second_order.json()["id"]
    order_id = first_order.json()["id"]
    assert first_order.json()["status"] == "pending_payment"

    changed_request = order_request()
    changed_request["shipping_address"]["address"] = "广州市天河区不同地址 2 号"
    conflicting_order = client.post(
        "/api/v1/orders",
        json=changed_request,
        headers=auth_headers(customer_token),
    )
    assert conflicting_order.status_code == 409

    inventory = session.get(SkuInventory, UUID(sku_id))
    assert inventory is not None
    assert inventory.on_hand == 5
    assert inventory.reserved == 2

    first_payment = client.post(
        f"/api/v1/orders/{order_id}/payments/simulated",
        json={"idempotency_key": "pay-key-001", "succeed": True},
        headers=auth_headers(customer_token),
    )
    second_payment = client.post(
        f"/api/v1/orders/{order_id}/payments/simulated",
        json={"idempotency_key": "pay-key-001", "succeed": True},
        headers=auth_headers(customer_token),
    )
    assert first_payment.status_code == 200
    assert second_payment.status_code == 200
    assert first_payment.json()["id"] == second_payment.json()["id"]
    assert first_payment.json()["status"] == "succeeded"
    assert first_payment.json()["order"]["status"] == "paid_pending_shipment"

    session.expire_all()
    inventory = session.get(SkuInventory, UUID(sku_id))
    reservations = session.exec(select(InventoryReservation)).all()
    assert inventory is not None
    assert inventory.on_hand == 3
    assert inventory.reserved == 0
    assert reservations[0].status == ReservationStatus.CONSUMED
    assert len(session.exec(select(Payment)).all()) == 1
    assert not session.exec(select(CartItem)).all()


def test_customer_cancel_pending_order_releases_inventory(
    client: TestClient,
    session: Session,
) -> None:
    _product_id, sku_id, _merchant_id = seed_published_product(client, session, stock=3)
    customer_token = create_customer_token(client, session, suffix="cancel")
    client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 2, "selected": True},
        headers=auth_headers(customer_token),
    )
    order_response = client.post(
        "/api/v1/orders",
        json=order_request("order-cancel-001"),
        headers=auth_headers(customer_token),
    )
    assert order_response.status_code == 201

    cancel_response = client.post(
        f"/api/v1/orders/{order_response.json()['id']}/cancel",
        json={"reason": "changed my mind"},
        headers=auth_headers(customer_token),
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "closed"
    assert cancel_response.json()["close_reason"] == "customer_cancelled"
    inventory = session.get(SkuInventory, UUID(sku_id))
    reservation = session.exec(select(InventoryReservation)).first()
    assert inventory is not None
    assert inventory.reserved == 0
    assert reservation is not None
    assert reservation.status == ReservationStatus.RELEASED


def test_checkout_blocks_insufficient_stock(
    client: TestClient,
    session: Session,
) -> None:
    _product_id, sku_id, _merchant_id = seed_published_product(client, session, stock=1)
    customer_token = create_customer_token(client, session, suffix="stock")
    add_response = client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 2, "selected": True},
        headers=auth_headers(customer_token),
    )
    assert add_response.status_code == 201

    order_response = client.post(
        "/api/v1/orders",
        json=order_request("order-stock-001"),
        headers=auth_headers(customer_token),
    )

    assert order_response.status_code == 409
    detail = order_response.json()["detail"]
    assert detail["message"] == "checkout blocked"
    assert "only 1 available" in detail["blockers"][0]


def test_expire_unpaid_orders_releases_inventory_and_is_admin_only(
    client: TestClient,
    session: Session,
) -> None:
    _product_id, sku_id, _merchant_id = seed_published_product(client, session, stock=2)
    customer_token = create_customer_token(client, session, suffix="expire")
    admin_token = create_admin_token(client, session)
    client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 1, "selected": True},
        headers=auth_headers(customer_token),
    )
    order_response = client.post(
        "/api/v1/orders",
        json=order_request("order-expire-001"),
        headers=auth_headers(customer_token),
    )
    assert order_response.status_code == 201
    order = session.get(Order, UUID(order_response.json()["id"]))
    assert order is not None
    order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.add(order)
    session.commit()

    customer_expire = client.post(
        "/api/v1/admin/orders/expire-unpaid",
        json={"limit": 10},
        headers=auth_headers(customer_token),
    )
    assert customer_expire.status_code == 403

    admin_expire = client.post(
        "/api/v1/admin/orders/expire-unpaid",
        json={"limit": 10},
        headers=auth_headers(admin_token),
    )

    assert admin_expire.status_code == 200
    assert admin_expire.json()["count"] == 1
    session.expire_all()
    order = session.get(Order, UUID(order_response.json()["id"]))
    inventory = session.get(SkuInventory, UUID(sku_id))
    assert order is not None
    assert order.status == OrderStatus.CLOSED
    assert order.close_reason == "payment_timeout"
    assert inventory is not None
    assert inventory.reserved == 0


def test_order_visibility_for_customer_merchant_and_admin(
    client: TestClient,
    session: Session,
) -> None:
    merchant_id = uuid4()
    _product_id, sku_id, _merchant_id = seed_published_product(
        client,
        session,
        merchant_id=merchant_id,
        stock=2,
    )
    customer_token = create_customer_token(client, session, suffix="scope")
    other_customer_token = create_customer_token(client, session, suffix="other")
    merchant_token = create_merchant_token(client, session, merchant_id)
    other_merchant_token = create_merchant_token(client, session, uuid4())
    admin_token = create_admin_token(client, session)
    client.post(
        "/api/v1/cart/items",
        json={"sku_id": sku_id, "quantity": 1, "selected": True},
        headers=auth_headers(customer_token),
    )
    order_response = client.post(
        "/api/v1/orders",
        json=order_request("order-scope-001"),
        headers=auth_headers(customer_token),
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    assert (
        client.get(f"/api/v1/orders/{order_id}", headers=auth_headers(other_customer_token))
        .status_code
        == 403
    )
    assert (
        client.get(f"/api/v1/merchant/orders/{order_id}", headers=auth_headers(merchant_token))
        .status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/merchant/orders/{order_id}",
            headers=auth_headers(other_merchant_token),
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/admin/orders/{order_id}",
            headers=auth_headers(admin_token),
        ).status_code
        == 200
    )
    audit_logs = session.exec(select(AuditLog).where(AuditLog.action == "order.create")).all()
    assert audit_logs
