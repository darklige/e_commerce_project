import { LoginShell } from "@/components/login-shell";

export default function MerchantForgotPasswordPage() {
  return (
    <LoginShell
      audience="商家"
      mode="forgot"
      accountType="merchant"
      eyebrow="Merchant Password Recovery"
      title="找回商家账号密码"
      description="商家密码重置会按 merchant 账号类型校验，避免误用普通用户或管理员账号。"
      accentClassName="bg-commerce-teal"
      primaryHref="/merchant/login"
      registerHref="/merchant/register"
      forgotHref="/merchant/forgot-password"
      loginHref="/merchant/login"
    />
  );
}
