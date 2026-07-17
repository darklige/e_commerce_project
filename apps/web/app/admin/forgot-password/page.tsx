import { LoginShell } from "@/components/login-shell";

export default function AdminForgotPasswordPage() {
  return (
    <LoginShell
      audience="管理员"
      mode="forgot"
      accountType="admin"
      eyebrow="Admin Password Recovery"
      title="找回管理员账号密码"
      description="管理员密码重置会按 admin 账号类型校验，并保留审计；生产环境应配合 MFA 和人工复核。"
      accentClassName="bg-commerce-gold"
      primaryHref="/admin/login"
      registerHref="/admin/register"
      forgotHref="/admin/forgot-password"
      loginHref="/admin/login"
    />
  );
}
