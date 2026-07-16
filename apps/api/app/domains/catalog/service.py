from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.domains.catalog.models import (
    Brand,
    Category,
    InventoryReservation,
    Product,
    ProductStatus,
    ReservationStatus,
    Sku,
    SkuInventory,
    utc_now,
)
from app.domains.catalog.schemas import (
    BrandCreate,
    CategoryCreate,
    InventoryAdjustmentRequest,
    InventoryReservationRequest,
    ProductCreate,
    ProductDetail,
    ProductListItem,
    ProductListResponse,
    ProductUpdate,
    SkuCreate,
    SkuPublic,
    SkuUpdate,
)


class CatalogError(Exception):
    pass


class CatalogNotFoundError(CatalogError):
    pass


class CatalogConflictError(CatalogError):
    pass


class CatalogPermissionError(CatalogError):
    pass


class InventoryInsufficientError(CatalogError):
    pass


class InventoryAdjustmentError(CatalogError):
    pass


@dataclass(frozen=True)
class ProductFilters:
    q: str | None = None
    category_id: UUID | None = None
    brand_id: UUID | None = None
    min_price_cents: int | None = None
    max_price_cents: int | None = None
    only_published: bool = True
    merchant_id: UUID | None = None


def create_category(session: Session, payload: CategoryCreate) -> Category:
    category = Category(**payload.model_dump())
    session.add(category)
    commit_or_conflict(session, "category already exists")
    session.refresh(category)
    return category


def list_categories(session: Session) -> list[Category]:
    statement = (
        select(Category)
        .where(Category.is_active == True)  # noqa: E712
        .order_by(Category.sort_order, Category.name)
    )
    return list(session.exec(statement).all())


def create_brand(session: Session, payload: BrandCreate) -> Brand:
    brand = Brand(**payload.model_dump())
    session.add(brand)
    commit_or_conflict(session, "brand already exists")
    session.refresh(brand)
    return brand


def list_brands(session: Session) -> list[Brand]:
    statement = select(Brand).where(Brand.is_active == True).order_by(Brand.name)  # noqa: E712
    return list(session.exec(statement).all())


def create_product(session: Session, merchant_id: UUID, payload: ProductCreate) -> ProductDetail:
    require_category(session, payload.category_id)
    if payload.brand_id is not None:
        require_brand(session, payload.brand_id)

    now = utc_now()
    prices = [sku.price_cents for sku in payload.skus]
    product = Product(
        merchant_id=merchant_id,
        category_id=payload.category_id,
        brand_id=payload.brand_id,
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
        main_image_url=payload.main_image_url,
        min_price_cents=min(prices),
        max_price_cents=max(prices),
        created_at=now,
        updated_at=now,
    )
    session.add(product)
    session.flush()

    for sku_payload in payload.skus:
        create_sku_row(session, product, sku_payload)

    commit_or_conflict(session, "sku code already exists for merchant")
    session.refresh(product)
    return get_product_detail(
        session,
        product.id,
        merchant_id=merchant_id,
        include_unpublished=True,
    )


def update_product(
    session: Session,
    merchant_id: UUID,
    product_id: UUID,
    payload: ProductUpdate,
) -> ProductDetail:
    product = require_product(session, product_id, merchant_id=merchant_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        require_category(session, update_data["category_id"])
    if update_data.get("brand_id") is not None:
        require_brand(session, update_data["brand_id"])

    for field_name, value in update_data.items():
        setattr(product, field_name, value)
    product.updated_at = utc_now()
    session.add(product)
    session.commit()
    session.refresh(product)
    return get_product_detail(
        session,
        product.id,
        merchant_id=merchant_id,
        include_unpublished=True,
    )


def add_sku(
    session: Session,
    merchant_id: UUID,
    product_id: UUID,
    payload: SkuCreate,
) -> ProductDetail:
    product = require_product(session, product_id, merchant_id=merchant_id)
    create_sku_row(session, product, payload)
    refresh_product_price_range(session, product)
    commit_or_conflict(session, "sku code already exists for merchant")
    return get_product_detail(
        session,
        product.id,
        merchant_id=merchant_id,
        include_unpublished=True,
    )


def update_sku(
    session: Session,
    merchant_id: UUID,
    sku_id: UUID,
    payload: SkuUpdate,
) -> SkuPublic:
    sku = require_sku(session, sku_id, merchant_id=merchant_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(sku, field_name, value)
    sku.updated_at = utc_now()
    session.add(sku)
    product = require_product(session, sku.spu_id, merchant_id=merchant_id)
    refresh_product_price_range(session, product)
    session.commit()
    return build_sku_public(session, sku)


def publish_product(session: Session, merchant_id: UUID, product_id: UUID) -> ProductDetail:
    product = require_product(session, product_id, merchant_id=merchant_id)
    active_skus = session.exec(
        select(Sku).where(
            Sku.spu_id == product.id,
            Sku.merchant_id == merchant_id,
            Sku.is_active == True,  # noqa: E712
        )
    ).all()
    if not active_skus:
        raise CatalogConflictError("product must have at least one active sku")
    product.status = ProductStatus.PUBLISHED
    product.updated_at = utc_now()
    session.add(product)
    session.commit()
    return get_product_detail(
        session,
        product.id,
        merchant_id=merchant_id,
        include_unpublished=True,
    )


def unpublish_product(session: Session, merchant_id: UUID, product_id: UUID) -> ProductDetail:
    product = require_product(session, product_id, merchant_id=merchant_id)
    product.status = ProductStatus.UNPUBLISHED
    product.updated_at = utc_now()
    session.add(product)
    session.commit()
    return get_product_detail(
        session,
        product.id,
        merchant_id=merchant_id,
        include_unpublished=True,
    )


def list_products(
    session: Session,
    filters: ProductFilters,
    *,
    offset: int,
    limit: int,
) -> ProductListResponse:
    statement = select(Product)
    count_statement = select(func.count()).select_from(Product)
    conditions = []
    if filters.only_published:
        conditions.append(Product.status == ProductStatus.PUBLISHED)
    if filters.merchant_id is not None:
        conditions.append(Product.merchant_id == filters.merchant_id)
    if filters.category_id is not None:
        conditions.append(Product.category_id == filters.category_id)
    if filters.brand_id is not None:
        conditions.append(Product.brand_id == filters.brand_id)
    if filters.min_price_cents is not None:
        conditions.append(Product.max_price_cents >= filters.min_price_cents)
    if filters.max_price_cents is not None:
        conditions.append(Product.min_price_cents <= filters.max_price_cents)
    if filters.q:
        conditions.append(col(Product.title).ilike(f"%{filters.q}%"))

    for condition in conditions:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = session.exec(count_statement).one()
    items = session.exec(
        statement.order_by(Product.updated_at.desc()).offset(offset).limit(limit)
    ).all()
    return ProductListResponse(
        items=[build_product_list_item(session, item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_product_detail(
    session: Session,
    product_id: UUID,
    *,
    merchant_id: UUID | None = None,
    include_unpublished: bool = False,
) -> ProductDetail:
    product = require_product(session, product_id, merchant_id=merchant_id)
    if not include_unpublished and product.status != ProductStatus.PUBLISHED:
        raise CatalogNotFoundError("product not found")

    skus = session.exec(
        select(Sku).where(Sku.spu_id == product.id, Sku.is_active == True).order_by(Sku.spec_name)  # noqa: E712
    ).all()
    list_item = build_product_list_item(session, product)
    return ProductDetail(
        **list_item.model_dump(),
        description=product.description,
        skus=[build_sku_public(session, sku) for sku in skus],
    )


def adjust_inventory(
    session: Session,
    merchant_id: UUID,
    payload: InventoryAdjustmentRequest,
) -> SkuPublic:
    sku = require_sku(session, payload.sku_id, merchant_id=merchant_id)
    inventory = require_inventory(session, sku.id, merchant_id=merchant_id)
    if inventory.on_hand + payload.delta < inventory.reserved:
        raise InventoryAdjustmentError("on hand stock cannot fall below reserved stock")
    inventory.on_hand += payload.delta
    inventory.version += 1
    inventory.updated_at = utc_now()
    session.add(inventory)
    session.commit()
    session.refresh(inventory)
    return build_sku_public(session, sku)


def list_inventory(
    session: Session,
    merchant_id: UUID,
    *,
    offset: int,
    limit: int,
) -> list[SkuPublic]:
    skus = session.exec(
        select(Sku)
        .where(Sku.merchant_id == merchant_id)
        .order_by(Sku.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [build_sku_public(session, sku) for sku in skus]


def reserve_inventory(
    session: Session,
    merchant_id: UUID,
    payload: InventoryReservationRequest,
) -> tuple[InventoryReservation, int]:
    sku = require_sku(session, payload.sku_id, merchant_id=merchant_id)
    existing = session.exec(
        select(InventoryReservation).where(
            InventoryReservation.merchant_id == merchant_id,
            InventoryReservation.idempotency_key == payload.idempotency_key,
        )
    ).first()
    if existing is not None:
        if existing.sku_id != sku.id or existing.quantity != payload.quantity:
            raise CatalogConflictError("idempotency key conflicts with another reservation")
        inventory = require_inventory(session, sku.id, merchant_id=merchant_id)
        return existing, inventory.on_hand - inventory.reserved

    result = session.exec(
        update(SkuInventory)
        .where(
            SkuInventory.sku_id == sku.id,
            SkuInventory.merchant_id == merchant_id,
            SkuInventory.on_hand - SkuInventory.reserved >= payload.quantity,
        )
        .values(
            reserved=SkuInventory.reserved + payload.quantity,
            version=SkuInventory.version + 1,
            updated_at=utc_now(),
        )
    )
    if result.rowcount != 1:
        session.rollback()
        raise InventoryInsufficientError("insufficient available stock")

    reservation = InventoryReservation(
        sku_id=sku.id,
        merchant_id=merchant_id,
        idempotency_key=payload.idempotency_key,
        quantity=payload.quantity,
        status=ReservationStatus.RESERVED,
    )
    session.add(reservation)
    commit_or_conflict(session, "idempotency key already exists")
    inventory = require_inventory(session, sku.id, merchant_id=merchant_id)
    return reservation, inventory.on_hand - inventory.reserved


def create_sku_row(session: Session, product: Product, payload: SkuCreate) -> Sku:
    sku = Sku(
        spu_id=product.id,
        merchant_id=product.merchant_id,
        sku_code=payload.sku_code,
        spec_name=payload.spec_name,
        price_cents=payload.price_cents,
        list_price_cents=payload.list_price_cents,
    )
    session.add(sku)
    session.flush()
    session.add(
        SkuInventory(
            sku_id=sku.id,
            merchant_id=product.merchant_id,
            on_hand=payload.initial_stock,
            reserved=0,
        )
    )
    return sku


def refresh_product_price_range(session: Session, product: Product) -> None:
    prices = session.exec(
        select(Sku.price_cents).where(Sku.spu_id == product.id, Sku.is_active == True)  # noqa: E712
    ).all()
    if not prices:
        product.min_price_cents = 0
        product.max_price_cents = 0
    else:
        product.min_price_cents = min(prices)
        product.max_price_cents = max(prices)
    product.updated_at = utc_now()
    session.add(product)


def build_product_list_item(session: Session, product: Product) -> ProductListItem:
    total_available = session.exec(
        select(func.coalesce(func.sum(SkuInventory.on_hand - SkuInventory.reserved), 0))
        .join(Sku, Sku.id == SkuInventory.sku_id)
        .where(
            Sku.spu_id == product.id,
            Sku.is_active == True,  # noqa: E712
        )
    ).one()
    return ProductListItem(
        id=product.id,
        merchant_id=product.merchant_id,
        category_id=product.category_id,
        brand_id=product.brand_id,
        title=product.title,
        subtitle=product.subtitle,
        status=product.status,
        main_image_url=product.main_image_url,
        min_price_cents=product.min_price_cents,
        max_price_cents=product.max_price_cents,
        total_available=total_available,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def build_sku_public(session: Session, sku: Sku) -> SkuPublic:
    inventory = require_inventory(session, sku.id, merchant_id=sku.merchant_id)
    return SkuPublic(
        id=sku.id,
        sku_code=sku.sku_code,
        spec_name=sku.spec_name,
        price_cents=sku.price_cents,
        list_price_cents=sku.list_price_cents,
        is_active=sku.is_active,
        on_hand=inventory.on_hand,
        reserved=inventory.reserved,
        available=inventory.on_hand - inventory.reserved,
    )


def require_category(session: Session, category_id: UUID) -> Category:
    category = session.get(Category, category_id)
    if category is None or not category.is_active:
        raise CatalogNotFoundError("category not found")
    return category


def require_brand(session: Session, brand_id: UUID) -> Brand:
    brand = session.get(Brand, brand_id)
    if brand is None or not brand.is_active:
        raise CatalogNotFoundError("brand not found")
    return brand


def require_product(
    session: Session,
    product_id: UUID,
    *,
    merchant_id: UUID | None = None,
) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise CatalogNotFoundError("product not found")
    if merchant_id is not None and product.merchant_id != merchant_id:
        raise CatalogPermissionError("product belongs to another merchant")
    return product


def require_sku(session: Session, sku_id: UUID, *, merchant_id: UUID | None = None) -> Sku:
    sku = session.get(Sku, sku_id)
    if sku is None:
        raise CatalogNotFoundError("sku not found")
    if merchant_id is not None and sku.merchant_id != merchant_id:
        raise CatalogPermissionError("sku belongs to another merchant")
    return sku


def require_inventory(session: Session, sku_id: UUID, *, merchant_id: UUID) -> SkuInventory:
    inventory = session.get(SkuInventory, sku_id)
    if inventory is None:
        raise CatalogNotFoundError("inventory not found")
    if inventory.merchant_id != merchant_id:
        raise CatalogPermissionError("inventory belongs to another merchant")
    return inventory


def commit_or_conflict(session: Session, message: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise CatalogConflictError(message) from exc
