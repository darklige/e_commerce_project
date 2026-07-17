import { LoginShell } from "@/components/login-shell";

export default function MerchantRegisterPage() {
  return (
    <LoginShell
      audience="商家"
      mode="register"
      accountType="merchant"
      eyebrow="Merchant Registration"
      title="注册商家账号，进入店铺运营工作台"
      description="商家账号会绑定商家范围，用于商品发布、库存维护、订单履约和售后审核。"
      accentClassName="bg-commerce-teal"
      primaryHref="/merchant/products"
      forgotHref="/merchant/forgot-password"
      loginHref="/merchant/login"
    />
  );
}
