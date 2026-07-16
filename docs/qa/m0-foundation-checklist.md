# M0 Foundation Checklist

本清单用于验收 `release/milestone-0-foundation`。

## Git 与协作

- 功能开发不在 `main` 上进行。
- M0 功能分支来自 `develop`。
- M0 完成后创建 `release/milestone-0-foundation`，回归通过后打 `v0.1.0-m0`。
- 提交和推送远端后再进入下一阶段。

## Monorepo 骨架

- `apps/api`：FastAPI 后端骨架。
- `apps/web`：Next.js + Tailwind CSS Web 骨架。
- `apps/android`：Android/Compose 工程骨架。
- `infra/docker`：PostgreSQL 和 API 的 Compose 配置。
- `.github/workflows/ci.yml`：CI 初版。
- `.env.example`：本地环境变量示例，不包含真实密钥。
- `scripts/verify-m0.sh`：本地验证入口。

## 验证命令

```bash
./scripts/verify-m0.sh
```

API：

```bash
cd apps/api
uv run ruff check .
uv run pytest
```

Web：

```bash
cd apps/web
npm run lint
npm run typecheck
npm run build
npm audit --omit=dev
```

Docker：

```bash
docker compose -f infra/docker/docker-compose.yml up --build
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
```

Android：

```bash
gradle -p apps/android :app:assembleDebug
```

当前开发机缺少 `android` CLI、Java Runtime 和 Gradle，因此 Android 构建在本地跳过。后续应在安装 JDK、Android SDK/CLI、Gradle 或 Gradle Wrapper 后补跑 `lint`、`test`、`assembleDebug`，并在 release 验收记录中附命令输出或 CI 链接。

## M0 通过标准

- API lint 和 health 测试通过。
- Web lint、typecheck、production build 通过。
- `npm audit --omit=dev` 无生产依赖漏洞。
- Docker Compose 配置有效，PostgreSQL 和 API 能启动。
- Android 骨架文件完整；若无法本地构建，必须清楚记录工具链限制。
- README 能指导新协作者启动项目。

