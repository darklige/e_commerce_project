# E-Commerce Platform

一个类京东的大型多端电商平台，采用 FastAPI + PostgreSQL + React/Next.js/Tailwind CSS + Android 的前后端分离架构。

当前阶段：M3 购物车、订单、模拟支付。

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

## M3 功能入口

API：

- 公开浏览：`GET /api/v1/categories`、`GET /api/v1/brands`、`GET /api/v1/products`、`GET /api/v1/products/{id}`。
- 商家商品：`POST /api/v1/merchant/products`、上下架、SKU 修改。
- 商家库存：`GET /api/v1/merchant/inventory`、库存调整、幂等库存预留。
- 管理员基础目录：`POST /api/v1/admin/categories`、`POST /api/v1/admin/brands`。
- 用户购物车：`GET /api/v1/cart`、添加/修改/删除购物车项。
- 结算：`POST /api/v1/checkout/preview`，每次重新校验商品、价格和库存。
- 用户订单：`POST /api/v1/orders`、订单列表/详情、待支付取消、模拟支付。
- 商家订单：`GET /api/v1/merchant/orders`、`GET /api/v1/merchant/orders/{id}`，按 `merchant_ids` 限定数据范围。
- 管理员订单：订单查询和 `POST /api/v1/admin/orders/expire-unpaid` 支付超时关闭任务入口。

Web：

- 用户商品浏览：`/products`
- 用户商品详情：`/products/northstar-x1`
- 用户购物车：`/cart`
- 用户结算：`/checkout`
- 用户订单：`/orders`、`/orders/order-20260716001`
- 商家商品管理：`/merchant/products`

当前 M2 审核策略：平台审核工作流暂不实现，商家调用 publish 后商品直接公开可售。后续 M4 会补平台运营审核和违规下架工作台。

当前 M3 支付策略：使用模拟支付，不接真实第三方渠道；订单创建会锁定库存，支付成功消费锁定库存，用户取消或支付超时会释放锁定库存。发货、收货、售后和退款在 M4 深化。

本地回归：

```bash
./scripts/verify-m0.sh
```

该脚本当前覆盖 API Ruff/pytest/Alembic SQL、Web lint/type/build、Android lint/test/assembleDebug。

## 协作规则

所有开发必须先阅读 `AGENTS.md`，按 `develop`、`codex/<area>/<task>`、`release/milestone-x` 的分支模型协作。每个阶段完成后必须提交并推送远端仓库。
