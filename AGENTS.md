# AGENTS.md

本文件是本仓库所有 Codex agent、子 agent 和人工协作者的共同工作协议。进入仓库后先读本文件，再读 `docs/DEVELOPMENT_PLAN.md` 和与当前任务相关的 ADR、接口文档、测试说明。

## 项目目标

本项目要构建一个类似京东的大型电商平台，覆盖：

- 用户网页端：React + Next.js + Tailwind CSS。
- Android App：面向普通用户的移动购物体验。
- 管理员后台：平台客服、运营、风控、财务、技术管理员等角色。
- 商家后台：店铺、商品、订单、发货、售后、结算等能力。
- 后端服务：FastAPI + PostgreSQL，前后端分离，通过 OpenAPI 契约协同。

开发重点不是堆功能数量，而是把选定业务流程做深。订单、履约、售后、权限、客服介入、审计和多端状态一致性必须按真实业务方式设计、实现和反复验证。

## 必须使用 Git 协同

- 禁止直接在 `main` 上开发功能。
- `main` 永远保持可发布；`develop` 是日常集成分支。
- 每个 agent 从 `develop` 拉自己的分支，分支名使用 `codex/<area>/<short-task>`，例如 `codex/backend/order-state-machine`。
- 一个阶段开发完成后，必须提交 commit、推送到远端仓库，并通过 PR 合并回 `develop`。
- 阶段验收完成后，从 `develop` 创建 `release/milestone-x`，完成回归、修复、打 tag，再合并到 `main` 并推送远端。
- 不要重置、回滚、覆盖他人改动。遇到冲突先读代码和提交历史，再最小化合并。
- 提交信息使用约定式提交，例如 `feat(order): add refund state machine`、`test(api): cover inventory reservation`。

推荐长期分支：

- `main`：生产可发布版本，只接受 release/hotfix 合并。
- `develop`：集成分支，所有功能 PR 的目标分支。
- `release/milestone-0-foundation`：M0 基建验收。
- `release/milestone-1-identity-rbac`：M1 账号与权限验收。
- `release/milestone-2-catalog-inventory`：M2 商品与库存验收。
- `release/milestone-3-order-after-sales`：M3 订单与售后验收。
- `release/milestone-4-admin-merchant`：M4 商家后台与管理员后台验收。
- `release/milestone-5-hardening-launch`：M5 稳定化发布。

推荐功能分支：

- `codex/backend/foundation-api`：FastAPI 项目骨架、健康检查、配置、日志、数据库连接。
- `codex/backend/identity-rbac`：账号、认证、RBAC、审计。
- `codex/backend/catalog-inventory`：SPU/SKU、类目、库存锁定和扣减。
- `codex/backend/order-workflow`：购物车、结算、订单、支付模拟、状态机。
- `codex/backend/after-sales`：退款、退货、客服介入、工单。
- `codex/web/user-shopping`：用户网页端浏览、购物车、下单、订单。
- `codex/web/admin-console`：平台管理员后台。
- `codex/web/merchant-console`：商家后台。
- `codex/android/user-app`：Android 用户端。
- `codex/infra/docker-ci`：Docker Compose、CI、环境变量、部署脚本。
- `codex/qa/e2e-contracts`：契约测试、E2E、回归用例和测试数据。

## Multi-Agent 分工

建议使用 multi-agent 并行推进，但每个 agent 必须有清晰边界，避免多人同时编辑同一文件。

- `backend-agent`：负责 `apps/api`、`libs/python_common`、`db/migrations`、OpenAPI 契约。
- `web-user-agent`：负责 `apps/web` 中用户前台页面和用户流程。
- `web-admin-agent`：负责管理员后台和平台运营/客服/风控/财务工作台。
- `web-merchant-agent`：负责商家后台、商品运营、发货、售后处理。
- `android-agent`：负责 `apps/android`，包含登录、商品、购物车、订单、售后移动端体验。
- `infra-agent`：负责 `infra`、CI、Docker、部署、环境模板。
- `qa-agent`：负责 `docs/qa`、测试策略、Playwright、API 契约、Android 测试。
- `docs-agent`：负责 `docs`、ADR、接口说明、流程图和发布说明。

每个 agent 开工前必须说明：

- 当前任务目标。
- 读过哪些文档和代码。
- 本次计划修改的文件范围。
- 预计验证方式。

每个 agent 收工前必须说明：

- 修改了哪些文件。
- 跑了哪些命令或测试。
- 未完成事项和风险。
- 是否已经 commit、push，PR 目标分支是什么。

## 业务深度要求

订单与售后是本项目核心深水区。实现时必须回答这些问题：

- 当前操作的发起人是谁：用户、商家员工、平台客服、风控、财务还是系统任务。
- 当前角色是否有权限操作该订单、子订单、售后单或退款单。
- 操作后哪些端需要看到状态变化。
- 是否需要通知另一方。
- 是否需要审计日志、理由、凭证、二次确认或审批。
- 超时未处理时系统如何自动推进。
- 出现争议时平台客服能看到什么、能做什么、不能做什么。

售后流程不能只做“申请、同意、退款成功”。至少要考虑：

- 商家拒绝后用户补充凭证或申请客服介入。
- 商家超时不处理时自动同意或升级工单。
- 用户超时不退货时关闭售后。
- 商家超时不确认收货时自动确认。
- 支付渠道退款失败后的重试和人工处理。
- 部分退款、运费、优惠券分摊、组合商品退款。
- 每个状态迁移的幂等、审计和消息通知。

## 技术约定

后端：

- 使用 FastAPI，优先遵循 `fastapi` skill：`Annotated` 依赖声明、router 级 prefix/tags/dependencies、清晰的返回类型或 `response_model`。
- 使用 PostgreSQL；所有 schema 变化必须通过 migration，不允许手工改生产数据。
- OpenAPI 是前后端契约来源；接口变更必须同步类型生成、调用方和文档。
- 阻塞代码不要放进 `async` path operation；不确定时使用普通 `def`。
- 关键流程要有幂等键、事务边界、审计日志和状态机测试。

前端：

- 使用 React + Next.js + Tailwind CSS。
- 用户端、管理员后台、商家后台可以共用 monorepo，但导航、权限、信息密度和交互风格要区分。
- 后台页面优先信息密度、可扫描、可批量操作；不要做营销页式大 Hero。
- 所有按钮、表单、表格、弹窗、空状态、错误状态和加载状态必须完整。

Android：

- 优先使用现代 Android/Compose 方案。
- 涉及窗口适配、边到边、导航、测试时使用相应 Android skills。
- 核心购物链路必须覆盖登录态过期、网络失败、支付回跳、订单状态刷新。

安全：

- 密钥和真实凭证禁止提交。
- `.env.example` 只放示例值。
- 用户、商家、管理员必须做接口权限、数据范围权限和字段脱敏。
- 退款、改价、关闭订单、客服裁决等敏感操作必须审计。

## 质量门禁

每个 PR 至少满足：

- 代码格式化、lint、类型检查通过。
- 后端单元测试和必要集成测试通过。
- Web 构建通过，关键页面可用。
- Android 模块至少能构建或说明未构建原因。
- DB migration 可升级；高风险 migration 需要 downgrade 或回滚方案。
- API 变更有 OpenAPI diff 和调用方同步。
- 涉及用户主流程的变更有 E2E 或明确的回归清单。

合并到 release 分支前还需要：

- 订单、售后、权限、库存并发等核心用例全量回归。
- 初始化数据和演示账号可用。
- 发布说明、已知问题和回滚方案齐全。

## 推荐使用的 Skills

本项目最常用：

- `fastapi`：后端 API、依赖、路由、响应模型。
- `playwright` / `playwright-interactive`：Web 端真实浏览器调试和 E2E。
- `testing-setup`：Android 测试体系。
- `android-cli`、`navigation-3`、`android-compose-adaptive`、`edge-to-edge`：Android 工程、导航和适配。
- `security-best-practices`、`security-threat-model`、`security-ownership-map`：安全编码、威胁建模、敏感代码责任图。
- `figma-*`：如果后续接入 Figma 设计稿或设计系统。
- `gh-fix-ci`、`gh-address-comments`：处理 GitHub Actions 和 PR review。
- `vercel-deploy`：用户 Web 或后台需要部署到 Vercel 时使用。
- `sentry`：接入或排查生产错误监控时使用。

完整可用 skills 清单见 `docs/SKILLS.md`。

