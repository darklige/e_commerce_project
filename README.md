# E-Commerce Platform

一个类京东的大型多端电商平台，采用 FastAPI + PostgreSQL + React/Next.js/Tailwind CSS + Android 的前后端分离架构。

当前阶段：M2 商品与库存。

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

## M2 功能入口

API：

- 公开浏览：`GET /api/v1/categories`、`GET /api/v1/brands`、`GET /api/v1/products`、`GET /api/v1/products/{id}`。
- 商家商品：`POST /api/v1/merchant/products`、上下架、SKU 修改。
- 商家库存：`GET /api/v1/merchant/inventory`、库存调整、幂等库存预留。
- 管理员基础目录：`POST /api/v1/admin/categories`、`POST /api/v1/admin/brands`。

Web：

- 用户商品浏览：`/products`
- 用户商品详情：`/products/northstar-x1`
- 商家商品管理：`/merchant/products`

当前 M2 审核策略：平台审核工作流暂不实现，商家调用 publish 后商品直接公开可售。后续 M4 会补平台运营审核和违规下架工作台。

本地回归：

```bash
./scripts/verify-m0.sh
```

该脚本当前覆盖 API Ruff/pytest/Alembic SQL、Web lint/type/build、Android lint/test/assembleDebug。

## 协作规则

所有开发必须先阅读 `AGENTS.md`，按 `develop`、`codex/<area>/<task>`、`release/milestone-x` 的分支模型协作。每个阶段完成后必须提交并推送远端仓库。
