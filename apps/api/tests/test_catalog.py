from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.domains.catalog.models import InventoryReservation, SkuInventory
from app.domains.catalog.schemas import (
    BrandCreate,
    CategoryCreate,
    InventoryReservationRequest,
    ProductCreate,
    SkuCreate,
)
from app.domains.catalog.service import (
    InventoryInsufficientError,
    create_brand,
    create_category,
    create_product,
    reserve_inventory,
)
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


def create_admin_token(client: TestClient, session: Session) -> str:
    create_user(
        session,
        email="catalog-admin@example.com",
        password="StrongerPass123!",
        display_name="Catalog Admin",
        account_type=AccountType.ADMIN,
        roles=[Role.ADMIN_OPERATOR],
    )
    return login(client, "catalog-admin@example.com", "StrongerPass123!", "admin")


def create_merchant_token(client: TestClient, session: Session, merchant_id: UUID) -> str:
    create_user(
        session,
        email=f"merchant-{merchant_id}@example.com",
        password="StrongerPass123!",
        display_name="Merchant",
        account_type=AccountType.MERCHANT,
        roles=[Role.MERCHANT_PRODUCT_OPERATOR],
        merchant_id=merchant_id,
    )
    return login(client, f"merchant-{merchant_id}@example.com", "StrongerPass123!", "merchant")


def create_catalog_seed(client: TestClient, admin_token: str) -> tuple[str, str]:
    category_response = client.post(
        "/api/v1/admin/categories",
        json={"name": "手机数码", "slug": "phones", "sort_order": 10},
        headers=auth_headers(admin_token),
    )
    assert category_response.status_code == 201
    brand_response = client.post(
        "/api/v1/admin/brands",
        json={"name": "Northstar", "slug": "northstar"},
        headers=auth_headers(admin_token),
    )
    assert brand_response.status_code == 201
    return category_response.json()["id"], brand_response.json()["id"]


def product_payload(category_id: str, brand_id: str) -> dict:
    return {
        "category_id": category_id,
        "brand_id": brand_id,
        "title": "Northstar X1",
        "subtitle": "旗舰性能手机",
        "description": "M2 demo product",
        "main_image_url": "https://example.com/x1.png",
        "skus": [
            {
                "sku_code": "NS-X1-BLACK-256",
                "spec_name": "曜石黑 / 256GB",
                "price_cents": 399900,
                "list_price_cents": 429900,
                "initial_stock": 5,
            },
            {
                "sku_code": "NS-X1-SILVER-512",
                "spec_name": "星银 / 512GB",
                "price_cents": 459900,
                "initial_stock": 2,
            },
        ],
    }


def test_merchant_product_flow_and_public_catalog(
    client: TestClient,
    session: Session,
) -> None:
    admin_token = create_admin_token(client, session)
    merchant_token = create_merchant_token(client, session, uuid4())
    category_id, brand_id = create_catalog_seed(client, admin_token)

    create_response = client.post(
        "/api/v1/merchant/products",
        json=product_payload(category_id, brand_id),
        headers=auth_headers(merchant_token),
    )
    assert create_response.status_code == 201
    product = create_response.json()
    assert product["status"] == "draft"
    assert product["total_available"] == 7

    public_before_publish = client.get("/api/v1/products")
    assert public_before_publish.status_code == 200
    assert public_before_publish.json()["total"] == 0

    publish_response = client.post(
        f"/api/v1/merchant/products/{product['id']}/publish",
        headers=auth_headers(merchant_token),
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    public_after_publish = client.get("/api/v1/products", params={"q": "Northstar"})
    assert public_after_publish.status_code == 200
    assert public_after_publish.json()["total"] == 1
    assert public_after_publish.json()["items"][0]["min_price_cents"] == 399900

    detail_response = client.get(f"/api/v1/products/{product['id']}")
    assert detail_response.status_code == 200
    assert len(detail_response.json()["skus"]) == 2


def test_customer_cannot_manage_catalog_or_inventory(
    client: TestClient,
    session: Session,
) -> None:
    create_user(
        session,
        email="buyer-m2@example.com",
        password="StrongerPass123!",
        display_name="Buyer",
        account_type=AccountType.CUSTOMER,
    )
    token = login(client, "buyer-m2@example.com", "StrongerPass123!", "customer")

    response = client.post(
        "/api/v1/merchant/products",
        json={},
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_inventory_adjust_reserve_idempotency_and_audit(
    client: TestClient,
    session: Session,
) -> None:
    admin_token = create_admin_token(client, session)
    merchant_id = uuid4()
    merchant_token = create_merchant_token(client, session, merchant_id)
    category_id, brand_id = create_catalog_seed(client, admin_token)
    product_response = client.post(
        "/api/v1/merchant/products",
        json=product_payload(category_id, brand_id),
        headers=auth_headers(merchant_token),
    )
    sku = next(
        item
        for item in product_response.json()["skus"]
        if item["sku_code"] == "NS-X1-BLACK-256"
    )
    sku_id = sku["id"]

    adjust_response = client.post(
        "/api/v1/merchant/inventory/adjustments",
        json={"sku_id": sku_id, "delta": 3, "reason": "cycle count"},
        headers=auth_headers(merchant_token),
    )
    assert adjust_response.status_code == 200
    assert adjust_response.json()["on_hand"] == 8

    reservation_body = {
        "sku_id": sku_id,
        "quantity": 4,
        "idempotency_key": "checkout-draft-001",
    }
    first_reserve = client.post(
        "/api/v1/merchant/inventory/reservations",
        json=reservation_body,
        headers=auth_headers(merchant_token),
    )
    second_reserve = client.post(
        "/api/v1/merchant/inventory/reservations",
        json=reservation_body,
        headers=auth_headers(merchant_token),
    )
    assert first_reserve.status_code == 200
    assert second_reserve.status_code == 200
    assert first_reserve.json()["reservation_id"] == second_reserve.json()["reservation_id"]

    inventory = session.get(SkuInventory, UUID(sku_id))
    assert inventory is not None
    assert inventory.reserved == 4
    audit_logs = session.exec(
        select(AuditLog).where(AuditLog.action == "catalog.inventory_adjust")
    ).all()
    assert audit_logs


def test_merchant_cannot_adjust_another_merchant_sku(
    client: TestClient,
    session: Session,
) -> None:
    admin_token = create_admin_token(client, session)
    first_merchant_token = create_merchant_token(client, session, uuid4())
    second_merchant_token = create_merchant_token(client, session, uuid4())
    category_id, brand_id = create_catalog_seed(client, admin_token)
    product_response = client.post(
        "/api/v1/merchant/products",
        json=product_payload(category_id, brand_id),
        headers=auth_headers(first_merchant_token),
    )
    sku_id = product_response.json()["skus"][0]["id"]

    response = client.post(
        "/api/v1/merchant/inventory/adjustments",
        json={"sku_id": sku_id, "delta": 1, "reason": "wrong merchant"},
        headers=auth_headers(second_merchant_token),
    )

    assert response.status_code == 403


def test_inventory_reservation_concurrency_does_not_oversell(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path}/inventory.db",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    SQLModel.metadata.create_all(engine)
    merchant_id = uuid4()
    with Session(engine) as session:
        category = create_category(
            session,
            CategoryCreate(name="并发类目", slug="concurrency"),
        )
        brand = create_brand(session, BrandCreate(name="并发品牌", slug="concurrency-brand"))
        product = create_product(
            session,
            merchant_id,
            ProductCreate(
                category_id=category.id,
                brand_id=brand.id,
                title="Limited SKU",
                skus=[
                    SkuCreate(
                        sku_code="LIMITED-001",
                        spec_name="标准版",
                        price_cents=9900,
                        initial_stock=5,
                    )
                ],
            ),
        )
        sku_id = product.skus[0].id

    def reserve_once(index: int) -> bool:
        with Session(engine) as session:
            try:
                reserve_inventory(
                    session,
                    merchant_id,
                    InventoryReservationRequest(
                        sku_id=sku_id,
                        quantity=1,
                        idempotency_key=f"parallel-{index:02d}",
                    ),
                )
            except InventoryInsufficientError:
                return False
            return True

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(reserve_once, range(8)))

    with Session(engine) as session:
        inventory = session.get(SkuInventory, sku_id)
        reservations = session.exec(select(InventoryReservation)).all()

    assert results.count(True) == 5
    assert results.count(False) == 3
    assert inventory is not None
    assert inventory.reserved == 5
    assert inventory.on_hand - inventory.reserved == 0
    assert len(reservations) == 5
