# M1 RBAC 权限矩阵

本矩阵用于 M1 账号与权限阶段。权限分为菜单权限、接口权限、数据范围权限、字段权限，并要求敏感操作全部写入审计日志。

| 角色 | 核心允许 | 核心禁止 |
|---|---|---|
| 普通用户 | 注册/登录、本人资料、本人订单、本人售后 | 查看他人数据、进入商家/管理员后台 |
| 会员用户 | 普通用户能力、会员权益 | 越权访问其他等级权益 |
| 企业用户 | 普通用户能力、企业采购扩展 | 查看其他企业主体数据 |
| 商家店主 | 店铺设置、员工管理、结算查看 | 跨店铺数据、平台配置 |
| 商品运营 | 商品发布、改价、库存维护 | 退款、提现、员工授权 |
| 订单客服 | 店铺订单查询、地址修改、售后初审 | 改价、结算、跨店铺处理 |
| 仓储发货 | 待发货订单、物流录入、面单打印 | 售后裁决、退款、财务数据 |
| 商家财务 | 账单、提现、发票、对账 | 商品/订单核心状态修改 |
| 超级管理员 | 权限分配、系统配置、审计查看 | 不得绕过审计 |
| 平台运营 | 类目、活动、商品审核 | 资金退款、系统权限分配 |
| 平台客服 | 工单处理、售后裁定、补偿券 | 商家结算、系统配置 |
| 客服主管 | 升级工单、批量复核 | 直接修改资金流水 |
| 风控审核 | 账号/订单/支付风险处置 | 普通运营配置、结算提现 |
| 财务管理员 | 退款复核、商家结算、渠道对账 | 商品审核、客服裁决 |
| 技术管理员 | 任务监控、日志查看、系统配置 | 直接处理业务资金 |
| 只读审计 | 查看日志和报表 | 任何写操作 |

## M1 API 权限映射

| API | 认证 | 需要权限 |
|---|---|---|
| `POST /api/v1/auth/register` | 否 | 仅允许普通用户自注册 |
| `POST /api/v1/auth/login` | 否 | 按 `account_type` 区分用户/商家/管理员入口 |
| `GET /api/v1/auth/me` | 是 | `user:profile:read` |
| `GET /api/v1/auth/admin/me` | 是 | `admin:console:access` |
| `GET /api/v1/auth/merchant/me` | 是 | `merchant:console:access` |

## M2 商品与库存 API 权限映射

| API | 认证 | 需要权限 | 数据范围 |
|---|---|---|---|
| `GET /api/v1/categories` | 否 | 公开 | 仅返回启用类目 |
| `GET /api/v1/brands` | 否 | 公开 | 仅返回启用品牌 |
| `GET /api/v1/products` | 否 | 公开 | 仅返回已上架商品 |
| `GET /api/v1/products/{product_id}` | 否 | 公开 | 未上架商品返回 `404` |
| `POST /api/v1/admin/categories` | 是 | `catalog:manage` | 管理员账号 |
| `POST /api/v1/admin/brands` | 是 | `catalog:manage` | 管理员账号 |
| `GET /api/v1/merchant/products` | 是 | `product:manage` | 当前商家 `merchant_ids` |
| `POST /api/v1/merchant/products` | 是 | `product:manage` | 当前商家 `merchant_ids` |
| `GET /api/v1/merchant/products/{product_id}` | 是 | `product:manage` | 禁止跨商家 |
| `PATCH /api/v1/merchant/products/{product_id}` | 是 | `product:manage` | 禁止跨商家 |
| `POST /api/v1/merchant/products/{product_id}/skus` | 是 | `product:manage` | 禁止跨商家 |
| `PATCH /api/v1/merchant/skus/{sku_id}` | 是 | `product:manage` | 禁止跨商家 |
| `POST /api/v1/merchant/products/{product_id}/publish` | 是 | `product:manage` | 禁止跨商家 |
| `POST /api/v1/merchant/products/{product_id}/unpublish` | 是 | `product:manage` | 禁止跨商家 |
| `GET /api/v1/merchant/inventory` | 是 | `inventory:manage` | 当前商家 `merchant_ids` |
| `POST /api/v1/merchant/inventory/adjustments` | 是 | `inventory:manage` | 禁止跨商家，写审计 |
| `POST /api/v1/merchant/inventory/reservations` | 是 | `inventory:manage` | 禁止跨商家，幂等键防重复预留 |

## M3 购物车、订单、模拟支付 API 权限映射

| API | 认证 | 需要权限 | 数据范围 |
|---|---|---|---|
| `GET /api/v1/cart` | 是 | `cart:manage` | 当前普通用户 |
| `POST /api/v1/cart/items` | 是 | `cart:manage` | 当前普通用户，只允许已上架 SKU |
| `PATCH /api/v1/cart/items/{cart_item_id}` | 是 | `cart:manage` | 禁止修改他人购物车项 |
| `DELETE /api/v1/cart/items/{cart_item_id}` | 是 | `cart:manage` | 禁止删除他人购物车项 |
| `POST /api/v1/checkout/preview` | 是 | `order:manage` | 当前普通用户选中购物车项 |
| `POST /api/v1/orders` | 是 | `order:manage` | 当前普通用户，幂等创建并锁库存 |
| `GET /api/v1/orders` | 是 | `order:manage` | 当前普通用户订单 |
| `GET /api/v1/orders/{order_id}` | 是 | `order:manage` | 禁止查看他人订单 |
| `POST /api/v1/orders/{order_id}/cancel` | 是 | `order:manage` | 仅本人待支付订单 |
| `POST /api/v1/orders/{order_id}/payments/simulated` | 是 | `order:manage` | 仅本人待支付订单，支付幂等 |
| `GET /api/v1/merchant/orders` | 是 | `order:manage` | 当前商家 `merchant_ids` |
| `GET /api/v1/merchant/orders/{order_id}` | 是 | `order:manage` | 禁止跨商家 |
| `GET /api/v1/admin/orders` | 是 | `order:manage` | 管理员账号 |
| `GET /api/v1/admin/orders/{order_id}` | 是 | `order:manage` | 管理员账号 |
| `POST /api/v1/admin/orders/expire-unpaid` | 是 | `order:manage` | 管理员账号，系统任务型敏感操作 |

## M4 售后、商家后台、管理员后台 API 权限映射

| API | 认证 | 需要权限 | 数据范围 |
|---|---|---|---|
| `POST /api/v1/after-sales` | 是 | `after_sales:manage` | 当前普通用户、本人已支付订单行 |
| `GET /api/v1/after-sales` | 是 | `after_sales:manage` | 当前普通用户售后 |
| `GET /api/v1/after-sales/{after_sales_id}` | 是 | `after_sales:manage` | 禁止查看他人售后 |
| `POST /api/v1/after-sales/{after_sales_id}/supplements` | 是 | `after_sales:manage` | 当前普通用户，补充凭证 |
| `POST /api/v1/after-sales/{after_sales_id}/return-shipment` | 是 | `after_sales:manage` | 当前普通用户，待买家退货状态 |
| `POST /api/v1/after-sales/{after_sales_id}/escalate` | 是 | `after_sales:manage` | 当前普通用户，生成/关联客服工单 |
| `POST /api/v1/after-sales/{after_sales_id}/cancel` | 是 | `after_sales:manage` | 当前普通用户，未退款前可撤销 |
| `GET /api/v1/merchant/after-sales` | 是 | `after_sales:manage` | 当前商家 `merchant_ids` |
| `GET /api/v1/merchant/after-sales/{after_sales_id}` | 是 | `after_sales:manage` | 禁止跨商家 |
| `POST /api/v1/merchant/after-sales/{after_sales_id}/approve` | 是 | `after_sales:manage` | 当前商家，写审核原因 |
| `POST /api/v1/merchant/after-sales/{after_sales_id}/reject` | 是 | `after_sales:manage` | 当前商家，写拒绝原因 |
| `POST /api/v1/merchant/after-sales/{after_sales_id}/confirm-receipt` | 是 | `after_sales:manage` | 当前商家，确认退货收货 |
| `GET /api/v1/admin/after-sales` | 是 | `after_sales:read` | 平台运营/客服/风控/财务/超级管理员可读 |
| `GET /api/v1/admin/after-sales/{after_sales_id}` | 是 | `after_sales:read` | 平台运营/客服/风控/财务/超级管理员可读 |
| `POST /api/v1/admin/after-sales/{after_sales_id}/decide` | 是 | `after_sales:decide` | 平台客服/主管/风控/超级管理员，必须写裁定原因 |
| `POST /api/v1/admin/after-sales/{after_sales_id}/retry-refund` | 是 | `after_sales:refund:retry` | 财务/超级管理员，退款失败后 |
| `POST /api/v1/admin/after-sales/auto-progress` | 是 | `after_sales:auto_progress` | 客服主管/超级管理员，系统任务型敏感操作 |
| `GET /api/v1/admin/work-orders` | 是 | `after_sales:read` | 平台运营/客服/风控/财务/超级管理员可读 |

## 审计要求

- 登录成功和失败都要记录。
- 注册成功和重复注册失败都要记录。
- 权限拒绝要记录操作人、缺失权限、请求 IP、User-Agent。
- 商品创建、商品修改、SKU 修改、上下架、库存调整、库存预留要记录操作人、对象和原因/参数。
- 购物车写操作、订单创建、取消、模拟支付、支付超时关闭要记录操作人、对象、状态事件和原因。
- 售后创建、商家同意/拒绝、用户补证、退货物流、客服介入、客服裁定、退款失败重试、超时推进要记录操作人、对象、状态事件、原因和凭证。
- 后续涉及改价、真实支付渠道退款和大额财务复核时必须记录前后状态、原因和凭证。
