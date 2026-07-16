# M5 Hardening And Launch Checklist

本清单用于 M5 稳定化发布前回归。M5 不再追求新增大功能，重点确认 M1-M4 的身份、商品库存、订单支付、售后工单、审计、安全和部署流程可以被重复验证。

## 1. 必跑命令

- `./scripts/verify-m0.sh`
- `./scripts/verify-m5.sh`
- `RUN_DOCKER_SMOKE=1 ./scripts/verify-m5.sh`（发布环境或有 Docker daemon 的机器执行完整 Compose smoke）
- `cd apps/api && uv run ruff check . && uv run pytest`
- `cd apps/api && uv run pytest tests/test_m5_e2e.py`
- `cd apps/api && uv run alembic upgrade head --sql >/tmp/commerce-m5-alembic-upgrade.sql`
- `cd apps/web && npm run lint && npm run typecheck && npm run build`
- `cd apps/android && ./gradlew lint test assembleDebug`

## 2. API 与数据迁移

- 健康检查 `/api/v1/health/live` 返回 200。
- 生产环境 `APP_ENV=production` 不暴露 `/openapi.json`、`/docs`、`/redoc`。
- 生产环境禁止默认 `JWT_SECRET_KEY`。
- `API_CORS_ORIGINS=*` 在携带凭证场景必须被拒绝。
- 不可信 Host 请求被 `TrustedHostMiddleware` 拒绝。
- Alembic 从空库生成完整升级 SQL，包含 M1-M4 所有 migration。
- Docker Compose 配置可解析；发布环境开启 `RUN_DOCKER_SMOKE=1` 时 API `/live` 和 `/ready` 通过。

## 3. 身份、权限与审计

- 普通用户可注册、登录、读取本人资料。
- 普通用户调用 API console guard（`/api/v1/auth/admin/me`、`/api/v1/auth/merchant/me`）返回 403。
- 商家和管理员分别只能通过 API console guard 进入对应 console 身份上下文。
- 商家账号只可访问绑定 `merchant_ids` 范围内的商品、订单、售后。
- 管理员售后权限按 `after_sales:read`、`after_sales:decide`、`after_sales:refund:retry`、`after_sales:auto_progress` 分离。
- 登录失败、权限拒绝、订单创建、库存调整、售后创建、客服裁决、退款重试均写审计日志。
- 审计日志截断用户可控长字段，避免日志膨胀和敏感数据扩散。

## 4. 商品、库存与购物车

- 商家可创建商品、SKU、初始库存并发布。
- 用户商品列表、商品详情可访问。
- 库存预留、释放、扣减在订单创建、取消、支付成功、超时关闭中保持一致。
- 重复库存预留幂等，不重复锁库存。
- 库存不足、商品下架、价格变化时结算预览阻止下单。

## 5. 订单与模拟支付

- 用户可从购物车生成订单，并保存商品、价格、地址快照。
- 订单创建使用 `customer_id + idempotency_key` 幂等。
- 模拟支付使用 `order_id + idempotency_key` 幂等。
- 待支付订单可取消并释放库存。
- 支付超时任务可重复执行，不重复关闭或重复释放库存。
- 支付成功订单进入 `paid_pending_shipment`，库存预留被消费。

## 6. 售后、退款与工单

- 仅退款可从 `paid_pending_shipment`、`shipped_awaiting_receipt`、`completed` 订单发起。
- 退货退款只允许 `shipped_awaiting_receipt` 或 `completed` 订单。
- 商家可同意、拒绝、确认退货收货；跨商家操作返回 403。
- 用户可补充凭证、填写退货物流、申请客服介入、撤销售后。
- 商家超时、用户超时退货、商家超时确认收货任务可重复执行且不重复退款。
- 退款失败后只有财务或超级管理员可重试。
- 客服工单展示队列、优先级、证据摘要、内部备注和裁定动作。

## 7. 全链路 E2E 与 Web 视觉检查

`apps/api/tests/test_m5_e2e.py` 覆盖当前可自动化的 API 级全链路：

- 用户注册、登录、读取本人资料。
- 普通用户访问管理员/商家 console guard 被拒绝。
- 管理员创建类目/品牌，商家创建并发布商品。
- 用户浏览商品、加入购物车、结算、下单、模拟支付。
- 商家读取订单和售后队列。
- 用户发起售后、商家拒绝、用户补充凭证并申请客服介入。
- 管理员查看工单并裁定退款，最终售后进入 `refunded`。
- 关键操作写入审计日志。

`./scripts/verify-m5.sh` 会用 Playwright CLI 访问：

- `/`
- `/products`
- `/cart`
- `/checkout`
- `/orders/order-20260716001`
- `/after-sales`
- `/after-sales/as-20260716001`
- `/merchant/after-sales`
- `/admin/work-orders`

检查重点：

- 页面不是空白页。
- 订单详情展示“申请售后”入口。
- 用户售后详情展示“申请客服介入”。
- 商家售后队列展示处理状态和操作入口。
- 管理员工单页展示“证据链”和内部备注。
- 宽表页面在窄屏通过横向滚动承载，不挤压正文。
- 当前 Web 是 demo-data 页面，M5 Playwright 只做页面可用性和关键文案烟测；真实 Web/API 登录联调不在本阶段自动化范围内。

## 8. Android

- Android 工程 `lint` 通过。
- Android 单元测试任务可执行，即使当前没有业务 unit test 也不能失败。
- `assembleDebug` 生成 debug 包。
- 后续接入真实 API 前，登录态过期、弱网、支付回跳、订单刷新、售后进度刷新必须补 instrumentation 或 screenshot tests。

## 9. 安全威胁模型

- 阅读 `docs/security/e_commerce_project-threat-model.md`。
- 所有 high/critical 风险必须有 owner、缓解计划或明确接受理由。
- 发布前至少确认 JWT secret、数据库凭证、CORS origin、allowed hosts、PostgreSQL 端口暴露策略。
- 真实支付、真实物流、文件上传、商家入驻资质上传上线前必须重新做威胁模型增量评审。

## 10. 部署与回滚

- 阅读 `docs/release/m5-hardening-launch.md`。
- release 分支从最新 `develop` 创建。
- release 分支只接受修复、文档和配置补充。
- tag 格式建议 `v0.5.0-m5`。
- 回滚优先回滚应用镜像；涉及 DB migration 时必须确认 migration 是否为向后兼容。
- 当前 M5 migration 均为建表型，回滚演示环境可重建数据库；生产环境不得直接 drop 有业务数据的表。

## 11. 已知限制

- Web 页面仍以 demo data 为主，尚未接 live API。
- Web 商家/管理员页面当前是演示工作台，没有真实前端鉴权中间件；console 权限以 API guard 和后端 RBAC 为准。
- 支付和退款仍为模拟渠道。
- 后台工单评论、通知、真实物流轨迹、商家结算和风控规则仍是后续深化项。
- Docker Compose 当前覆盖 PostgreSQL 和 API；Web/Android 发布管线需要后续接入正式部署平台。
