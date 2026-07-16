# OpenAPI Change Log

## 2026-07-16 - M3 Cart Order And Simulated Payment

新增用户购物车接口：

- `GET /api/v1/cart`
- `POST /api/v1/cart/items`
- `PATCH /api/v1/cart/items/{cart_item_id}`
- `DELETE /api/v1/cart/items/{cart_item_id}`

新增结算与订单接口：

- `POST /api/v1/checkout/preview`
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/cancel`
- `POST /api/v1/orders/{order_id}/payments/simulated`

新增商家订单查询接口：

- `GET /api/v1/merchant/orders`
- `GET /api/v1/merchant/orders/{order_id}`

新增管理员订单治理接口：

- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/{order_id}`
- `POST /api/v1/admin/orders/expire-unpaid`

权限变更：

- 新增 `cart:manage`、`order:manage`。
- 普通用户可管理本人购物车和订单。
- 商家店主、订单客服、仓储发货可按 `merchant_ids` 查看本店订单。
- 平台运营、客服、风控、财务和超级管理员可查询订单；当前 M3 仅管理员可触发未支付超时关闭。

状态与幂等：

- 订单状态包含 `pending_payment`、`paid_pending_shipment`、`closed`。
- 订单创建使用 `customer_id + idempotency_key` 幂等。
- 模拟支付使用 `order_id + idempotency_key` 幂等。
- 库存预留在订单创建时生成，支付成功消费预留，取消/超时释放预留。

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
