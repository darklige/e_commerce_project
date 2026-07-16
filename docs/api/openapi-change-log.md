# OpenAPI Change Log

## 2026-07-16 - M2 Catalog And Inventory

新增公开商品浏览接口：

- `GET /api/v1/categories`
- `GET /api/v1/brands`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`

新增管理员类目/品牌基础维护接口：

- `POST /api/v1/admin/categories`
- `POST /api/v1/admin/brands`

新增商家商品与库存接口：

- `GET /api/v1/merchant/products`
- `POST /api/v1/merchant/products`
- `GET /api/v1/merchant/products/{product_id}`
- `PATCH /api/v1/merchant/products/{product_id}`
- `POST /api/v1/merchant/products/{product_id}/skus`
- `PATCH /api/v1/merchant/skus/{sku_id}`
- `POST /api/v1/merchant/products/{product_id}/publish`
- `POST /api/v1/merchant/products/{product_id}/unpublish`
- `GET /api/v1/merchant/inventory`
- `POST /api/v1/merchant/inventory/adjustments`
- `POST /api/v1/merchant/inventory/reservations`

权限变更：

- 新增 `catalog:manage`、`product:manage`、`inventory:manage`。
- 商家商品运营可管理商品和库存。
- 商家仓储可管理库存。
- 平台运营可管理类目/品牌。
