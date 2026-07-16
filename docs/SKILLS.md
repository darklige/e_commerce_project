# 可用 Skills 清单

本文件列出当前环境中可用或已安装的 Codex skills，并标注哪些最适合本电商项目。新增安装的 skills 会在下一轮对话中按 Codex 规则触发。

## 本项目强相关 Skills

- `fastapi`：FastAPI API、Pydantic、依赖注入、路由、响应模型。
- `playwright`：真实浏览器自动化、页面调试、E2E 流程验证。
- `playwright-interactive`：持久浏览器会话，适合反复调试 Web UI。
- `testing-setup`：Android 测试策略、UI test、screenshot test、E2E。
- `android-cli`：Android CLI、工程创建、运行、设备管理。
- `navigation-3`：Android Navigation 3、深链、多 backstack、登录态导航。
- `android-compose-adaptive`：Compose 多窗口、多设备、折叠屏、桌面适配。
- `android-compose-styles`：Compose Styles API 和组件主题。
- `edge-to-edge`：Android edge-to-edge 适配。
- `android-intent-security`：Android Intent 安全审查。
- `r8-analyzer`：Android R8/Proguard 规则和包体优化。
- `security-best-practices`：Python、JavaScript/TypeScript、Go 安全最佳实践。
- `security-threat-model`：仓库级威胁建模，适合 M5 前安全评审。
- `security-ownership-map`：敏感代码 ownership 和 bus factor 分析。
- `gh-fix-ci`：排查 GitHub Actions 失败。
- `gh-address-comments`：处理 GitHub PR review comments。
- `vercel-deploy`：部署 Next.js Web 或后台到 Vercel。
- `sentry`：查询和分析 Sentry 生产错误。

## 设计与前端协作 Skills

- `figma-use`：调用 Figma 工具前的强制前置 skill。
- `figma`：获取 Figma 设计上下文、截图、变量和资产。
- `figma-implement-design`：将 Figma 设计实现为生产 UI。
- `figma-generate-design`：把已有页面或应用布局写入 Figma。
- `figma-generate-library`：从代码库生成或更新设计系统。
- `figma-create-design-system-rules`：生成项目级设计规范。
- `figma-code-connect-components`：建立 Figma 组件与代码组件映射。
- `figma-create-new-file`：创建新的 Figma/FigJam 文件。
- `imagegen`：生成位图视觉资产、商品占位图、活动图等。
- `visualize`：创建交互式可视化、流程模拟、图表。

## 文档、表格和交付物 Skills

- `documents`：创建、编辑、校验 Word/docx 文档。
- `pdf`：读取、创建、渲染、校验 PDF。
- `Presentations`：创建或编辑 PowerPoint/Google Slides 演示文稿。
- `Spreadsheets`：创建、编辑、分析 xlsx/csv/tsv。
- `excel-live-control`：控制打开的 Excel 工作簿。
- `officecli`：用 CLI 创建、分析、修改 Office 文档。
- `template-creator`：创建可复用的个人 Codex artifact 模板。

## Codex 与工具扩展 Skills

- `openai-docs`：查询 OpenAI/Codex 官方文档和最新模型/API 信息。
- `skill-installer`：从官方 curated 列表或 GitHub 安装 Codex skills。
- `skill-creator`：创建或更新自定义 Codex skill。
- `plugin-creator`：创建 Codex plugin 目录和 manifest。
- `cli-creator`：从 API 文档、OpenAPI、SDK 或脚本创建 CLI。

## 浏览器和本机操作 Skills

- `control-in-app-browser`：控制 Codex 内置浏览器。
- `control-chrome`：控制用户 Chrome 浏览器。
- `computer-use`：通过 Computer Use 操作本机 Mac App UI。

## 评测、追踪和数据平台 Skills

这些 skills 偏向 Merlin/Seed/LangSmith/Langfuse 平台，不是本电商项目默认必需，但如果项目后续接入评测、追踪或内部平台可以使用。

- `langfuse`
- `langsmith-dataset`
- `langsmith-evaluator`
- `langsmith-trace`
- `custom-eval-set-merlin-integration`
- `merlin-arena`
- `merlin-checkpoints`
- `merlin-cli`
- `merlin-collection`
- `merlin-dashboards`
- `merlin-data`
- `merlin-devbox`
- `merlin-evals`
- `merlin-exercise`
- `merlin-grafana`
- `merlin-image`
- `merlin-insight`
- `merlin-job`
- `merlin-knowledge-qa`
- `merlin-logits`
- `merlin-model-card`
- `merlin-mojo`
- `merlin-profiling`
- `merlin-resource`
- `merlin-service`
- `merlin-tracking-experiment`
- `merlin-weave`

## Android 迁移类 Skills

- `agp-9-upgrade`：迁移 Android Gradle Plugin 9。
- `migrate-xml-views-to-jetpack-compose`：从 XML View 迁移到 Jetpack Compose。

## 本次已补充安装的 Skills

本次从官方 skills 仓库安装了以下适合本项目后续协作的 skills：

- `gh-fix-ci`
- `gh-address-comments`
- `security-threat-model`
- `security-ownership-map`
- `vercel-deploy`
- `sentry`

安装说明：GitHub API 列表接口命中限流，因此先通过 Git sparse checkout 核对官方 curated 目录，再使用 `skill-installer` 安装上述 skills。

## 后续建议自建的项目专用 Skills

随着项目推进，可以使用 `skill-creator` 创建项目专用 skills：

- `ecommerce-order-state-machine`：订单和售后状态机实现/审查规则。
- `ecommerce-rbac-audit`：用户、商家、管理员权限和审计检查。
- `ecommerce-openapi-contract`：OpenAPI 变更、类型生成、前后端契约检查。
- `ecommerce-release-checklist`：阶段 release、tag、远端推送、回归清单。

