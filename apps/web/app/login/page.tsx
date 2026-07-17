import { LoginShell } from "@/components/login-shell";

export default function UserLoginPage() {
  return (
    <LoginShell
      audience="用户"
      accountType="customer"
      eyebrow="User Shopping Login"
      title="登录后继续你的购物、订单和售后进度"
      description="用户账号用于浏览商品、同步购物车、查看订单、申请售后和追踪客服介入状态。"
      accentClassName="bg-commerce-red"
      primaryHref="/"
      registerHref="/register"
      forgotHref="/forgot-password"
      loginHref="/login"
    />
  );
}
