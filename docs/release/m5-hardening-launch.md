# M5 稳定化与发布手册

## M5 范围

M5 目标来自 `docs/DEVELOPMENT_PLAN.md`：性能、安全、审计、E2E、部署文档，完成演示数据和可部署版本。当前发布文档覆盖：

- 安全威胁模型：`docs/security/e_commerce_project-threat-model.md`。
- 部署前检查：分支、CI、配置、数据库、审计、回滚材料。
- 环境变量：API、PostgreSQL、Compose 需要的最小集合。
- 验证路径：Docker Compose、API 全链路 E2E、Web、Android、Playwright 页面烟测。
- 回滚方案：应用、数据库、配置和数据卷。
- release 分支/tag 流程：按 `AGENTS.md` 的 `develop -> release/* -> main` 协作规则。
- 已知限制：真实支付/退款、Web/API 集成、Android 功能等。

本手册不替代 QA 回归清单；M5 合并 release 前仍需执行 API 全链路 E2E、订单/售后/权限/库存并发回归、Web 页面烟测和已知问题签收。

## 部署前检查

| 检查项 | 要求 | 证据/命令 |
|---|---|---|
| 分支 | 从 `develop` 创建 `release/milestone-5-hardening-launch`，release 分支只接受修复和文档补充 | `git branch --show-current` |
| 工作区 | 发布前不能包含未确认的源码改动；并行 worker 的 `scripts/`、`docs/qa/` 改动需由对应 owner 验收 | `git status --short` |
| API 测试 | Ruff、pytest、Alembic SQL 通过 | `uv run --project apps/api ruff check .`、`uv run --project apps/api pytest`、`cd apps/api && uv run alembic upgrade head --sql >/tmp/alembic-upgrade.sql` |
| API 全链路 E2E | 用户注册登录、商家建品、购物车、下单、模拟支付、售后、客服介入、管理员裁定退款闭环通过 | `cd apps/api && uv run pytest tests/test_m5_e2e.py` |
| M5 一键验证 | 基线验证、Compose config、Playwright 页面烟测通过 | `./scripts/verify-m5.sh` |
| Docker smoke | 有 Docker daemon 的发布环境执行完整 Compose smoke | `RUN_DOCKER_SMOKE=1 ./scripts/verify-m5.sh` |
| Web 构建 | lint、typecheck、build 通过 | `cd apps/web && npm ci && npm run lint && npm run typecheck && npm run build` |
| Android 构建 | lint、unit test、assembleDebug 通过；如本机缺 SDK/JDK，需记录原因 | `cd apps/android && ./gradlew lint test assembleDebug` |
| CI | release 分支 PR 或 push 的 API/Web/Android jobs 全绿 | `.github/workflows/ci.yml` |
| API 契约 | OpenAPI 变更已记录，前端/Android 调用方同步或明确未接入 | `docs/api/openapi-change-log.md` |
| 安全配置 | production 不允许默认 JWT secret，不允许 `API_CORS_ORIGINS=*`，OpenAPI/docs 在 production 隐藏 | `apps/api/app/core/config.py`、`apps/api/tests/test_health.py` |
| 数据库 | migration 可生成 SQL；发布前完成备份和版本记录 | `apps/api/migrations/versions/**` |
| 审计 | 登录、权限拒绝、商品/库存/订单/售后关键写操作有测试或代码证据 | `apps/api/tests/test_auth.py`、`apps/api/tests/test_orders.py`、`apps/api/tests/test_after_sales.py` |
| 回滚材料 | 镜像/commit/tag、数据库备份、上一个稳定 tag、配置快照可用 | release checklist |

## 环境变量

API 读取 `pydantic-settings`，默认 `.env`。生产/共享环境必须显式覆盖示例值。

| 变量 | 用途 | M5 要求 |
|---|---|---|
| `APP_NAME` | 健康检查返回服务名 | 可用默认值 |
| `APP_ENV` | 控制 docs/openapi 是否暴露和生产 secret 校验 | 生产必须为 `production` |
| `APP_VERSION` | 健康检查和发布版本 | 与 release tag 对齐，例如 `0.5.0-m5` |
| `API_CORS_ORIGINS` | 允许浏览器来源，逗号分隔 | 生产只能列真实 Web 域名，不得为 `*` |
| `ALLOWED_HOSTS` | TrustedHost 白名单 | 生产列 API 域名、负载均衡 host 和健康检查 host |
| `JWT_SECRET_KEY` | HS256 JWT 签名密钥 | 生产必须由密钥管理系统生成，禁止使用 `.env.example` 默认值 |
| `JWT_ALGORITHM` | JWT 算法 | 当前实现为 `HS256`，变更需同步兼容策略 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | access token TTL | 管理员/商家建议短 TTL；当前全局默认 30 分钟 |
| `DATABASE_URL` | API 连接 PostgreSQL | 生产使用非默认账号、强密码、内网地址，建议启用 TLS |
| `POSTGRES_DB` | Compose Postgres 数据库名 | 本地/演示用 |
| `POSTGRES_USER` | Compose Postgres 用户 | 生产不得使用默认 `commerce` |
| `POSTGRES_PASSWORD` | Compose Postgres 密码 | 生产不得使用默认 `commerce` |
| `POSTGRES_PORT` | 本机映射端口 | 生产不应直接暴露数据库端口 |

Web 当前没有读取 API base URL 的代码，页面使用 `apps/web/lib/*-demo.ts`。如果 M5 后接入真实 API，应新增并记录 `NEXT_PUBLIC_API_BASE_URL` 或服务端环境变量，同时明确 token 存储策略。

Android 当前没有网络权限和 API client，`AndroidManifest.xml` 仅声明 launcher Activity。接入真实 API 前需补充 base URL、网络安全配置、token 安全存储和 release 签名策略。

## Docker Compose 验证

当前 Compose 用于本地 smoke：PostgreSQL + API。

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

或使用 M5 脚本执行完整 Compose smoke：

```bash
RUN_DOCKER_SMOKE=1 ./scripts/verify-m5.sh
```

验证：

```bash
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
```

预期：

- `/live` 返回 `status=ok`。
- `/ready` 能连接 Compose PostgreSQL 并返回 `database=ok`。
- Postgres 默认映射到 `localhost:${POSTGRES_PORT:-55432}`，避免和本机 `5432` 冲突。

重要限制：

- `infra/docker/Dockerfile.api` 已复制 `apps/api/alembic.ini` 和 `apps/api/migrations`，容器具备运行 Alembic migration 的文件条件；生产仍建议使用独立 migration job，避免多个 API 副本并发迁移。
- Compose 的 API 环境为 `APP_ENV=docker`，不会触发 `production` 默认 JWT secret 拒绝逻辑；共享环境必须显式设置强 `JWT_SECRET_KEY`，或改为 `APP_ENV=production` 并配置生产 CORS/hosts。
- Compose 默认数据库账号密码来自 `.env.example` 风格示例，只能用于本地。

发布建议：

- 使用独立 migration job 或一次性 release task 执行 Alembic。
- 生产不要暴露 Postgres 端口；API 通过内网连接数据库。
- 在部署平台层强制 HTTPS、请求限流和访问日志采集。

## API 验证

本地开发启动：

```bash
uv sync --project apps/api --group dev
uv run --project apps/api fastapi dev app/main.py
```

基础验证：

```bash
curl -fsS http://127.0.0.1:8000/api/v1/health/live
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
```

质量门禁：

```bash
uv run --project apps/api ruff check .
uv run --project apps/api pytest
cd apps/api
uv run alembic upgrade head --sql >/tmp/alembic-upgrade.sql
```

安全和 E2E 重点验证：

- production 默认密钥拒绝：`apps/api/tests/test_health.py::test_production_rejects_default_jwt_secret`。
- CORS wildcard 拒绝：`apps/api/tests/test_health.py::test_cors_rejects_wildcard_with_credentials`。
- security headers：`apps/api/tests/test_health.py::test_security_headers_are_set`。
- untrusted host 拒绝：`apps/api/tests/test_health.py::test_untrusted_host_is_rejected`。
- production 隐藏 OpenAPI/docs：`apps/api/tests/test_health.py::test_production_hides_api_schema`。
- 用户-商家-管理员全链路：`apps/api/tests/test_m5_e2e.py::test_m5_customer_to_merchant_to_admin_after_sales_e2e`。
- 登录、权限拒绝和审计：`apps/api/tests/test_auth.py`。
- 订单数据范围和审计：`apps/api/tests/test_orders.py`。
- 售后数据范围、自动推进和审计：`apps/api/tests/test_after_sales.py`。

## Web 验证

当前 Web 是 Next.js 应用，覆盖用户、商家、管理员页面，但使用 demo 数据和静态表单。

```bash
cd apps/web
npm ci
npm run lint
npm run typecheck
npm run build
npm run dev
```

人工 smoke 页面：

- 用户商品：`/products`
- 用户商品详情：`/products/northstar-x1`
- 购物车：`/cart`
- 结算：`/checkout`
- 用户订单：`/orders`、`/orders/order-20260716001`
- 用户售后：`/after-sales`、`/after-sales/as-20260716001`
- 商家登录：`/merchant/login`
- 商家商品：`/merchant/products`
- 商家售后：`/merchant/after-sales`
- 管理员登录：`/admin/login`
- 管理员工单：`/admin/work-orders`

M5 验收边界：

- 可验证页面布局、状态展示、信息密度和构建质量。
- 不能把 Web 操作视为已完成 API 联调；真实登录、token 存储、错误态和 API 异常处理仍是后续工作或独立验收项。
- 商家/管理员 Web 页面当前是 demo 工作台，未做真实前端鉴权中间件；console 权限以 API `/auth/admin/me`、`/auth/merchant/me` 和后端 RBAC 为准。

## Android 验证

当前 Android 是 M0 Compose 工程壳。

```bash
cd apps/android
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
./gradlew lint test assembleDebug
```

M5 验收边界：

- 可验证 Gradle、Compose、lint/test/build 基线。
- 当前 `AndroidManifest.xml` 没有 `INTERNET` 权限，`MainActivity.kt` 只展示 foundation shell。
- 不应声称 Android 已完成登录、商品、购物车、订单或售后真实链路。

## 回滚方案

### 应用回滚

1. 停止流量或把流量切回上一稳定版本。
2. 使用上一稳定 release tag 对应镜像/commit 重新部署。
3. 复核 `/api/v1/health/live` 和 `/api/v1/health/ready`。
4. 抽样验证登录、商品浏览、订单读取、售后读取。
5. 保留失败版本日志、审计日志和部署配置用于复盘。

### 数据库回滚

M5 前必须先备份数据库。当前 Alembic migration 有 downgrade 结构，但高风险数据变更仍应优先采用向前修复。

回滚顺序：

1. 记录当前 migration revision 和 release tag。
2. 备份 PostgreSQL 数据库或快照数据卷。
3. 如果新版本尚未写入不兼容数据，可执行 Alembic downgrade 到上一 revision。
4. 如果已经写入业务数据，优先发布兼容修复 migration，避免破坏订单、支付、售后、退款和审计事实。
5. 回滚后运行 API pytest 中订单/售后/权限核心测试，确认状态机和审计仍可读。

### 配置回滚

- 恢复上一版本 `.env` 或部署平台 secret 版本。
- 确认 `JWT_SECRET_KEY` 轮换影响：如果回滚到旧 key，会导致新 key 签发 token 失效；若发生泄露，应接受强制重新登录。
- 恢复 `API_CORS_ORIGINS` 和 `ALLOWED_HOSTS` 后验证 Web 域名和健康检查域名。

### Compose 数据卷回滚

本地/演示环境使用 `commerce_postgres_data` volume。删除 volume 会丢失数据，只能在确认不需要保留演示数据时执行。

```bash
docker compose -f infra/docker/docker-compose.yml down
docker volume ls | grep commerce_postgres_data
```

如需保留数据，先用 `pg_dump` 或 volume snapshot，再进行清理。

## Release 分支和 tag 流程

1. 从 `develop` 更新本地分支：

```bash
git checkout develop
git pull --ff-only origin develop
```

2. 创建 release 分支：

```bash
git checkout -b release/milestone-5-hardening-launch
git push -u origin release/milestone-5-hardening-launch
```

3. 只合入 M5 修复、文档补充、回归修复。禁止在 release 分支继续大功能开发。

4. 确认 CI 全绿、回归完成、发布说明和回滚方案签收。

5. 打 tag，示例：

```bash
git tag -a v0.5.0-m5 -m "release: milestone 5 hardening launch"
git push origin v0.5.0-m5
```

6. release 分支 PR 合并到 `main`，再把 `main` 合并回 `develop`，保证后续开发包含 release 修复。

7. 远端确认：

```bash
git ls-remote --heads origin main develop release/milestone-5-hardening-launch
git ls-remote --tags origin v0.5.0-m5
```

## 已知限制

| 限制 | 影响 | 后续动作 |
|---|---|---|
| 真实支付/退款未接入 | 当前模拟支付/退款不能代表渠道签名、回调重放、清结算和对账风险 | 接入前新增支付回调签名、幂等事件表、金额校验和财务复核 |
| Web 使用 demo 数据 | 不能验证真实登录、API 错误、token 存储和权限渲染 | 接 OpenAPI client，并补 Playwright E2E |
| Android 仅工程壳 | 不能验证移动端登录态过期、弱网、支付回跳和订单刷新 | 增加网络层、导航、ViewModel 测试和设备回归 |
| Compose 未内置 migration job | API 镜像具备 migration 文件，但 Compose 不会自动执行 DB upgrade | 发布平台增加一次性 Alembic migration job |
| 无登录限流/MFA 证据 | 管理员、商家和用户账号存在凭据填充风险 | 网关/API 限流，后台强制 MFA |
| 字段级脱敏未完全实现 | 商家/管理员列表和详情可能暴露完整地址/手机号 | 按角色拆 response model，敏感字段读取写审计 |
| Docker Compose 默认凭据 | 误用于共享环境会造成 DB/JWT 风险 | 共享环境必须使用强 secret，Postgres 不暴露公网 |
| CI 未做依赖漏洞扫描且 Action 未 pin SHA | 供应链风险未闭环 | 增加 osv/pip-audit/npm audit，pin actions 到 SHA |
| OpenAPI diff 未自动化 | API breaking change 主要依赖人工记录 | 增加 schema 导出和 diff gate |

## 发布签收摘要

M5 release 可以在以下条件满足后进入验收：

- API/Web/Android CI 全绿。
- Docker Compose health smoke 通过，并记录 migration job 执行方式。
- 安全威胁模型已更新并进入评审。
- 订单、售后、权限、库存并发等核心回归通过。
- 生产/演示环境变量不使用 `.env.example` 默认 secret。
- 数据库备份、回滚 tag、配置快照和已知限制已签收。
