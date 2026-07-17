import { LoginShell } from "@/components/login-shell";

export default function UserForgotPasswordPage() {
  return (
    <LoginShell
      audience="用户"
      mode="forgot"
      accountType="customer"
      eyebrow="Customer Password Recovery"
      title="找回用户账号密码"
      description="通过邮箱发起一次性密码重置，重置请求会按用户账号类型校验并写入审计。"
      accentClassName="bg-commerce-red"
      primaryHref="/login"
      registerHref="/register"
      forgotHref="/forgot-password"
      loginHref="/login"
    />
  );
}
