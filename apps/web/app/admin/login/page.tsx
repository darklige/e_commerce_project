import { LoginShell } from "@/components/login-shell";

export default function AdminLoginPage() {
  return (
    <LoginShell
      audience="管理员"
      eyebrow="Admin Console"
      title="平台治理工作台"
      description="面向平台客服、运营、风控、财务和技术管理员的统一后台入口。"
      accentClassName="bg-commerce-gold"
      accountType="admin"
      primaryHref="/admin/work-orders"
      registerHref="/admin/register"
      forgotHref="/admin/forgot-password"
      loginHref="/admin/login"
    />
  );
}
