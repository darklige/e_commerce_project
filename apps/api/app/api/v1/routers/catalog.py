from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.db.session import SessionDep
from app.domains.catalog.schemas import (
    BrandCreate,
    BrandPublic,
    CategoryCreate,
    CategoryPublic,
    InventoryAdjustmentRequest,
    InventoryReservationRequest,
    InventoryReservationResponse,
    ProductCreate,
    ProductDetail,
    ProductListResponse,
    ProductUpdate,
    SkuCreate,
    SkuPublic,
    SkuUpdate,
)
from app.domains.catalog.service import (
    CatalogConflictError,
    CatalogNotFoundError,
    CatalogPermissionError,
    InventoryAdjustmentError,
    InventoryInsufficientError,
    ProductFilters,
    add_sku,
    adjust_inventory,
    create_brand,
    create_category,
    create_product,
    get_product_detail,
    list_brands,
    list_categories,
    list_inventory,
    list_products,
    publish_product,
    reserve_inventory,
    unpublish_product,
    update_product,
    update_sku,
)
from app.domains.identity.audit import write_audit_log
from app.domains.identity.constants import AccountType, Permission
from app.domains.identity.dependencies import AuthContext, require_permissions

router = APIRouter(tags=["catalog"])

AdminCatalogDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.CATALOG_MANAGE,
            account_types=(AccountType.ADMIN,),
        )
    ),
]
MerchantProductDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.PRODUCT_MANAGE,
            account_types=(AccountType.MERCHANT,),
        )
    ),
]
MerchantInventoryDep = Annotated[
    AuthContext,
    Depends(
        require_permissions(
            Permission.INVENTORY_MANAGE,
            account_types=(AccountType.MERCHANT,),
        )
    ),
]


@router.get("/categories")
def read_categories(session: SessionDep) -> list[CategoryPublic]:
    return [
        CategoryPublic.model_validate(item, from_attributes=True)
        for item in list_categories(session)
    ]


@router.post("/admin/categories", status_code=status.HTTP_201_CREATED)
def create_admin_category(
    payload: CategoryCreate,
    request: Request,
    session: SessionDep,
    auth: AdminCatalogDep,
) -> CategoryPublic:
    try:
        category = create_category(session, payload)
    except CatalogConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    write_audit_log(
        session,
        request=request,
        action="catalog.category_create",
        resource_type="category",
        resource_id=str(category.id),
        outcome="success",
        actor_user_id=auth.user.id,
        details=payload.model_dump_json(),
    )
    session.commit()
    return CategoryPublic.model_validate(category, from_attributes=True)


@router.get("/brands")
def read_brands(session: SessionDep) -> list[BrandPublic]:
    return [BrandPublic.model_validate(item, from_attributes=True) for item in list_brands(session)]


@router.post("/admin/brands", status_code=status.HTTP_201_CREATED)
def create_admin_brand(
    payload: BrandCreate,
    request: Request,
    session: SessionDep,
    auth: AdminCatalogDep,
) -> BrandPublic:
    try:
        brand = create_brand(session, payload)
    except CatalogConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    write_audit_log(
        session,
        request=request,
        action="catalog.brand_create",
        resource_type="brand",
        resource_id=str(brand.id),
        outcome="success",
        actor_user_id=auth.user.id,
        details=payload.model_dump_json(),
    )
    session.commit()
    return BrandPublic.model_validate(brand, from_attributes=True)


@router.get("/products")
def read_products(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=120)] = None,
    category_id: UUID | None = None,
    brand_id: UUID | None = None,
    min_price_cents: Annotated[int | None, Query(ge=0)] = None,
    max_price_cents: Annotated[int | None, Query(ge=0)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ProductListResponse:
    return list_products(
        session,
        ProductFilters(
            q=q,
            category_id=category_id,
            brand_id=brand_id,
            min_price_cents=min_price_cents,
            max_price_cents=max_price_cents,
            only_published=True,
        ),
        offset=offset,
        limit=limit,
    )


@router.get("/products/{product_id}")
def read_product(session: SessionDep, product_id: UUID) -> ProductDetail:
    try:
        return get_product_detail(session, product_id)
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/merchant/products")
def read_merchant_products(
    session: SessionDep,
    auth: MerchantProductDep,
    q: Annotated[str | None, Query(max_length=120)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ProductListResponse:
    merchant_id = get_primary_merchant_id(auth)
    return list_products(
        session,
        ProductFilters(q=q, merchant_id=merchant_id, only_published=False),
        offset=offset,
        limit=limit,
    )


@router.post("/merchant/products", status_code=status.HTTP_201_CREATED)
def create_merchant_product(
    payload: ProductCreate,
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
) -> ProductDetail:
    merchant_id = get_primary_merchant_id(auth)
    try:
        product = create_product(session, merchant_id, payload)
    except (CatalogConflictError, CatalogNotFoundError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(
        session,
        request,
        auth,
        "catalog.product_create",
        product.id,
        payload.model_dump(),
    )
    return product


@router.get("/merchant/products/{product_id}")
def read_merchant_product(
    session: SessionDep,
    auth: MerchantProductDep,
    product_id: UUID,
) -> ProductDetail:
    try:
        return get_product_detail(
            session,
            product_id,
            merchant_id=get_primary_merchant_id(auth),
            include_unpublished=True,
        )
    except (CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc


@router.patch("/merchant/products/{product_id}")
def update_merchant_product(
    payload: ProductUpdate,
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
    product_id: UUID,
) -> ProductDetail:
    try:
        product = update_product(session, get_primary_merchant_id(auth), product_id, payload)
    except (CatalogConflictError, CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(
        session,
        request,
        auth,
        "catalog.product_update",
        product.id,
        payload.model_dump(),
    )
    return product


@router.post("/merchant/products/{product_id}/skus")
def create_merchant_sku(
    payload: SkuCreate,
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
    product_id: UUID,
) -> ProductDetail:
    try:
        product = add_sku(session, get_primary_merchant_id(auth), product_id, payload)
    except (CatalogConflictError, CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(
        session,
        request,
        auth,
        "catalog.sku_create",
        product.id,
        payload.model_dump(),
    )
    return product


@router.patch("/merchant/skus/{sku_id}")
def update_merchant_sku(
    payload: SkuUpdate,
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
    sku_id: UUID,
) -> SkuPublic:
    try:
        sku = update_sku(session, get_primary_merchant_id(auth), sku_id, payload)
    except (CatalogConflictError, CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(session, request, auth, "catalog.sku_update", sku.id, payload.model_dump())
    return sku


@router.post("/merchant/products/{product_id}/publish")
def publish_merchant_product(
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
    product_id: UUID,
) -> ProductDetail:
    try:
        product = publish_product(session, get_primary_merchant_id(auth), product_id)
    except (CatalogConflictError, CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(session, request, auth, "catalog.product_publish", product.id, {})
    return product


@router.post("/merchant/products/{product_id}/unpublish")
def unpublish_merchant_product(
    request: Request,
    session: SessionDep,
    auth: MerchantProductDep,
    product_id: UUID,
) -> ProductDetail:
    try:
        product = unpublish_product(session, get_primary_merchant_id(auth), product_id)
    except (CatalogConflictError, CatalogNotFoundError, CatalogPermissionError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(session, request, auth, "catalog.product_unpublish", product.id, {})
    return product


@router.get("/merchant/inventory")
def read_merchant_inventory(
    session: SessionDep,
    auth: MerchantInventoryDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SkuPublic]:
    return list_inventory(session, get_primary_merchant_id(auth), offset=offset, limit=limit)


@router.post("/merchant/inventory/adjustments")
def create_inventory_adjustment(
    payload: InventoryAdjustmentRequest,
    request: Request,
    session: SessionDep,
    auth: MerchantInventoryDep,
) -> SkuPublic:
    try:
        sku = adjust_inventory(session, get_primary_merchant_id(auth), payload)
    except (CatalogNotFoundError, CatalogPermissionError, InventoryAdjustmentError) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(
        session,
        request,
        auth,
        "catalog.inventory_adjust",
        sku.id,
        payload.model_dump(),
    )
    return sku


@router.post("/merchant/inventory/reservations")
def create_inventory_reservation(
    payload: InventoryReservationRequest,
    request: Request,
    session: SessionDep,
    auth: MerchantInventoryDep,
) -> InventoryReservationResponse:
    try:
        reservation, available = reserve_inventory(session, get_primary_merchant_id(auth), payload)
    except (
        CatalogConflictError,
        CatalogNotFoundError,
        CatalogPermissionError,
        InventoryInsufficientError,
    ) as exc:
        raise to_http_error(exc) from exc

    audit_product_action(
        session,
        request,
        auth,
        "catalog.inventory_reserve",
        reservation.sku_id,
        payload.model_dump(),
    )
    return InventoryReservationResponse(
        reservation_id=reservation.id,
        sku_id=reservation.sku_id,
        quantity=reservation.quantity,
        status=reservation.status,
        available=available,
    )


def get_primary_merchant_id(auth: AuthContext) -> UUID:
    if not auth.merchant_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="merchant scope required",
        )
    return auth.merchant_ids[0]


def to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CatalogNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, CatalogPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (CatalogConflictError, InventoryAdjustmentError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, InventoryInsufficientError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def audit_product_action(
    session: Session,
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
        resource_type="catalog",
        resource_id=str(resource_id),
        outcome="success",
        actor_user_id=auth.user.id,
        details=str(details),
    )
    session.commit()
