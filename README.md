# E-Commerce Platform

一个类京东的大型多端电商平台，采用 FastAPI + PostgreSQL + React/Next.js/Tailwind CSS + Android 的前后端分离架构。

当前阶段：M0 基建。

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
npm install
npm run dev
```

Docker Compose：

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

Compose 默认将 PostgreSQL 暴露到 `localhost:55432`，避免和本机已有 PostgreSQL 的 `5432` 端口冲突。

Android：

当前仓库包含 Android/Compose 工程骨架。需要安装 Android CLI、JDK 和 Gradle 后再进行本地构建验证。

## 协作规则

所有开发必须先阅读 `AGENTS.md`，按 `develop`、`codex/<area>/<task>`、`release/milestone-x` 的分支模型协作。每个阶段完成后必须提交并推送远端仓库。
