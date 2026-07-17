import { LoginShell } from "@/components/login-shell";

export default function AdminRegisterPage() {
  return (
    <LoginShell
      audience="管理员"
      mode="register"
      accountType="admin"
      eyebrow="Admin Invitation Registration"
      title="管理员账号需要平台邀请码"
      description="管理员账号不能开放自助提权，只能通过平台邀请码创建受限角色，并在后台继续做权限治理。"
      accentClassName="bg-commerce-gold"
      primaryHref="/admin/work-orders"
      forgotHref="/admin/forgot-password"
      loginHref="/admin/login"
    />
  );
}
