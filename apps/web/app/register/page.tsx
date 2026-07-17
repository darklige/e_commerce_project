import { LoginShell } from "@/components/login-shell";

export default function UserRegisterPage() {
  return (
    <LoginShell
      audience="用户"
      mode="register"
      accountType="customer"
      eyebrow="Customer Registration"
      title="创建用户账号，开始完整购物体验"
      description="用户账号可自助注册，用于购物车、订单、模拟支付和售后进度追踪。"
      accentClassName="bg-commerce-red"
      primaryHref="/"
      forgotHref="/forgot-password"
      loginHref="/login"
    />
  );
}
