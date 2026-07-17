# E-Commerce Platform

一个类京东的大型多端电商平台，采用 FastAPI + PostgreSQL + React/Next.js/Tailwind CSS + Android 的前后端分离架构。

当前阶段：M5 稳定化与发布。

## 项目结构

```text
apps/
  api/       # FastAPI backend
  web/       # Next.js web app for user/admin/merchant surfaces
  android/   # Android user app skeleton
infra/
  docker/    # Docker Compose and Dockerfiles
docs/        # Planning, ADRs, API notes, QA checklists
scripts/     # Local verification helpers
```

## 快速开始

后端：

```bash
uv sync --project apps/api --group dev
uv run --project apps/api fastapi dev app/main.py
```

Web：

```bash
cd apps/web
npm ci
npm run dev
```

Docker Compose：

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

Compose 默认将 PostgreSQL 暴露到 `localhost:55432`，避免和本机已有 PostgreSQL 的 `5432` 端口冲突。

Android：

当前仓库包含 Android/Compose 工程骨架。需要安装 Android CLI、JDK 和 Gradle 后再进行本地构建验证。

## M5 功能入口与验证

API：

- 账号认证：用户/商家/管理员分端注册、按 `account_type` 登录、按账号类型找回密码。
- 公开浏览：`GET /api/v1/categories`、`GET /api/v1/brands`、`GET /api/v1/products`、`GET /api/v1/products/{id}`。
- 商家商品：`POST /api/v1/merchant/products`、上下架、SKU 修改。
- 商家库存：`GET /api/v1/merchant/inventory`、库存调整、幂等库存预留。
- 管理员基础目录：`POST /api/v1/admin/categories`、`POST /api/v1/admin/brands`。
- 用户购物车：`GET /api/v1/cart`、添加/修改/删除购物车项。
- 结算：`POST /api/v1/checkout/preview`，每次重新校验商品、价格和库存。
- 用户订单：`POST /api/v1/orders`、订单列表/详情、待支付取消、模拟支付。
- 商家订单：`GET /api/v1/merchant/orders`、`GET /api/v1/merchant/orders/{id}`，按 `merchant_ids` 限定数据范围。
- 管理员订单：订单查询和 `POST /api/v1/admin/orders/expire-unpaid` 支付超时关闭任务入口。
- 用户售后：创建售后、补充凭证、填写退货物流、申请客服介入、撤销售后。
- 商家售后：售后列表/详情、审核同意/拒绝、确认退货收货。
- 管理员售后：客服裁定、退款失败重试、超时自动推进、工单列表。

Web：

- 用户登录/注册/找回密码：`/login`、`/register`、`/forgot-password`
- 用户商品浏览：`/products`
- 用户商品详情：`/products/northstar-x1`
- 用户购物车：`/cart`
- 用户结算：`/checkout`
- 用户订单：`/orders`、`/orders/order-20260716001`
- 用户售后：`/after-sales`、`/after-sales/as-20260716001`
- 商家登录/注册/找回密码：`/merchant/login`、`/merchant/register`、`/merchant/forgot-password`
- 商家商品管理：`/merchant/products`
- 商家售后处理：`/merchant/after-sales`
- 管理员登录/邀请注册/找回密码：`/admin/login`、`/admin/register`、`/admin/forgot-password`
- 管理员客服工单：`/admin/work-orders`

本地 Web 未设置 `NEXT_PUBLIC_API_BASE_URL` 时，会按当前页面 hostname 自动调用
`http://<当前 hostname>:8000/api/v1`，避免 `localhost` 和 `127.0.0.1`
混用导致浏览器 CORS 拦截。如果 API 地址不同，可在启动 Web 前设置：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run dev
```

本地管理员邀请注册默认邀请码为 `local-admin-invite-code`，生产环境必须通过
`ADMIN_REGISTRATION_INVITE_CODE` 配置为独立密钥。

当前商品审核策略：平台审核工作流暂不实现，商家调用 publish 后商品直接公开可售。后续阶段会补平台运营审核和违规下架工作台。

当前 M4 售后策略：使用模拟退款，不接真实渠道；仅退款支持已支付未发货订单，退货退款要求已发货待收货或已完成订单。商家审核、用户退货、商家收货、客服介入、退款失败重试和超时推进均通过状态机、幂等键与审计日志串联；管理员权限拆分为售后只读、客服裁定、财务退款重试和主管超时任务。真实支付渠道、完整物流轨迹和大额财务复核流留到后续阶段深化。

当前 M5 稳定化策略：保留模拟支付/退款和 demo-data Web 页面，重点补齐安全威胁模型、发布回滚文档、M5 回归清单、API 全链路 E2E、安全硬化测试和 Playwright CLI 页面烟测。

本地回归：

```bash
./scripts/verify-m0.sh
./scripts/verify-m5.sh
```

`verify-m0.sh` 覆盖 API Ruff/pytest/Alembic SQL、Web lint/type/build、Android lint/test/assembleDebug，其中 API pytest 包含 `tests/test_m5_e2e.py` 的用户-商家-管理员全链路回归。`verify-m5.sh` 在此基础上启动 Web dev server，并用 Playwright CLI 检查用户、商家、管理员关键页面。

## 协作规则

所有开发必须先阅读 `AGENTS.md`，按 `develop`、`codex/<area>/<task>`、`release/milestone-x` 的分支模型协作。每个阶段完成后必须提交并推送远端仓库。
