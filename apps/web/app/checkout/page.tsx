import Link from "next/link";
import { MapPin, ShieldCheck, Truck, WalletCards } from "lucide-react";

import { PageHeader, StatusPill, UserCommerceShell } from "@/components/user-commerce";
import { formatPrice } from "@/lib/catalog-demo";
import { demoCartItems, selectedCartTotal } from "@/lib/order-demo";

export default function CheckoutPage() {
  const selectedItems = demoCartItems.filter((item) => item.selected);

  return (
    <UserCommerceShell active="cart">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow="结算"
          title="确认订单"
          description="确认收货信息、配送方式和支付金额。真实链路会在这里重新校验商品、价格、库存与地址可配送性。"
          action={
            <Link className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-bold" href="/cart">
              返回购物车
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
          <div className="grid gap-5">
            <section className="rounded-md border border-slate-200 bg-white p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <h2 className="flex items-center gap-2 text-lg font-black">
                  <MapPin className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                  收货信息
                </h2>
                <button className="w-fit rounded-md border border-slate-200 px-3 py-2 text-sm font-bold" type="button">
                  更换地址
                </button>
              </div>
              <div className="mt-4 grid gap-2 rounded-md bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-bold">张三 13800000000</p>
                <p>北京市朝阳区测试路 1 号</p>
                <p className="text-xs text-slate-500">地址快照会随订单保存，后续商品修改不会影响历史订单。</p>
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <h2 className="flex items-center gap-2 text-lg font-black">
                  <Truck className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                  配送与商品
                </h2>
                <StatusPill tone="teal">已重新计算</StatusPill>
              </div>
              <div className="mt-4 overflow-hidden rounded-md border border-slate-100">
                {selectedItems.map((item) => (
                  <article className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[88px_1fr_120px]" key={item.id}>
                    <div
                      aria-label={item.product.title}
                      className="aspect-square rounded-md bg-cover bg-center"
                      role="img"
                      style={{ backgroundImage: `url(${item.product.image})` }}
                    />
                    <div>
                      <h3 className="font-black">{item.product.title}</h3>
                      <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                      <p className="mt-2 text-xs text-commerce-teal">结算时已重算价格、库存和商品可售状态</p>
                    </div>
                    <div className="text-sm font-bold">
                      <p>{formatPrice(item.sku.price)}</p>
                      <p className="mt-1 text-slate-500">x {item.quantity}</p>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-5 md:grid-cols-3">
              {[
                { label: "模拟支付", value: "提交后进入待支付订单", icon: WalletCards },
                { label: "库存预占", value: "支付前保留库存，超时释放", icon: ShieldCheck },
                { label: "售后可追踪", value: "订单详情可申请售后", icon: Truck }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div className="rounded-md bg-slate-50 p-4" key={item.label}>
                    <Icon className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                    <p className="mt-3 text-sm font-black">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.value}</p>
                  </div>
                );
              })}
            </section>
          </div>

          <aside className="h-fit rounded-md border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-black">订单金额</h2>
            <div className="mt-5 grid gap-3 border-b border-slate-100 pb-4 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">商品金额</span>
                <span className="font-bold">{formatPrice(selectedCartTotal())}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">运费</span>
                <span className="font-bold">{formatPrice(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">优惠</span>
                <span className="font-bold text-commerce-teal">-{formatPrice(0)}</span>
              </div>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <span className="text-sm text-slate-600">应付</span>
              <span className="text-3xl font-black text-commerce-red">{formatPrice(selectedCartTotal())}</span>
            </div>
            <Link
              className="mt-5 flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-5 text-sm font-bold text-white"
              href="/orders/order-20260716002"
            >
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              提交订单
            </Link>
            <p className="mt-3 text-xs leading-5 text-slate-500">提交订单后会生成订单快照、库存预留和支付倒计时。</p>
          </aside>
        </div>
      </section>
    </UserCommerceShell>
  );
}
