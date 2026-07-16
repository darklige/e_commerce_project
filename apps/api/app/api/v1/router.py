from fastapi import APIRouter

from app.api.v1.routers.after_sales import router as after_sales_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.catalog import router as catalog_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.orders import router as orders_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(after_sales_router)
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(health_router)
api_router.include_router(orders_router)
