# M2 Catalog And Inventory Checklist

## API 验收

- `GET /api/v1/categories` 和 `GET /api/v1/brands` 返回启用数据。
- 公开商品列表和详情只展示 `published` 商品。
- 商家可以创建商品、添加 SKU、修改商品、上下架商品。
- 普通用户访问商家商品管理接口返回 `403`。
- 商家不能读取或调整其他商家的 SKU/库存。
- 库存调整不能让 `on_hand` 小于 `reserved`。
- 库存预留支持 `idempotency_key`，重复请求不重复占用库存。
- 库存不足返回 `409`，库存不能变负。
- 商品创建、上下架、库存调整和预留写入审计日志。

## 并发与事务

- 同一 SKU 多并发预留时不能超卖。
- 并发成功数量不得超过可售库存。
- 失败的库存预留不写入 reservation。
- Alembic migration 可生成 PostgreSQL 升级 SQL，并包含 downgrade。

## Web 验收

- `/products` 展示商品列表、搜索筛选、价格和可售库存。
- `/products/[id]` 展示 SKU 规格、价格、可售库存和失效提示位置。
- `/merchant/products` 展示商家商品表格、上下架操作区、库存预警和库存调整队列。
- Web lint、typecheck、build 通过。

## 当前策略

- M2 暂不实现平台审核工作流；商家调用 publish 后商品直接公开可售。
- Web 页面使用本地 demo 数据呈现交互结构，真实 API 接入留到后续契约类型生成后推进。
