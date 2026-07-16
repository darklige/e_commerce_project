# M1 Identity And RBAC Checklist

## API 验收

- 普通用户可以通过 `POST /api/v1/auth/register` 注册。
- 注册接口拒绝额外字段，不能通过公开接口创建管理员或商家账号。
- 重复邮箱返回 `409`。
- 弱密码由 Pydantic 长度规则拒绝。
- `POST /api/v1/auth/login` 按 `account_type` 登录，账号类型不匹配返回 `401`。
- `GET /api/v1/auth/me` 需要 Bearer token。
- 普通用户访问管理员/商家控制台接口返回 `403`。
- 管理员角色可以访问 `GET /api/v1/auth/admin/me`。
- 商家角色可以访问 `GET /api/v1/auth/merchant/me`。
- 登录失败、注册失败、权限拒绝均写入审计日志。

## Web 验收

- `/admin/login` 可构建并展示管理员登录入口。
- `/merchant/login` 可构建并展示商家登录入口。
- 页面不包含硬编码密钥，不使用危险 HTML 注入。

## 本地命令

```bash
./scripts/verify-m0.sh
```

该脚本在 M1 后继续作为基础回归入口，包含 API 测试、Web lint/type/build、Android lint/test/assembleDebug。
