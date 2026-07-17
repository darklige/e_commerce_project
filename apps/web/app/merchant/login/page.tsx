import { LoginShell } from "@/components/login-shell";

export default function MerchantLoginPage() {
  return (
    <LoginShell
      audience="商家"
      eyebrow="Merchant Console"
      title="店铺运营工作台"
      description="面向店主、商品运营、订单客服、仓储发货和商家财务的后台入口。"
      accentClassName="bg-commerce-teal"
      accountType="merchant"
      primaryHref="/merchant/products"
      registerHref="/merchant/register"
      forgotHref="/merchant/forgot-password"
      loginHref="/merchant/login"
    />
  );
}
