import Link from "next/link";

import { formatPrice } from "@/lib/catalog-demo";
import { demoCartItems, selectedCartTotal } from "@/lib/order-demo";

export default function CheckoutPage() {
  const selectedItems = demoCartItems.filter((item) => item.selected);

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto grid max-w-6xl gap-5 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-5">
          <header className="flex flex-col gap-3 border-b border-slate-200 pb-5">
            <Link className="text-sm font-semibold text-commerce-teal" href="/cart">
              返回购物车
            </Link>
            <div>
              <p className="text-sm font-semibold text-commerce-red">结算</p>
              <h1 className="mt-1 text-2xl font-semibold">确认订单</h1>
            </div>
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">收货信息</h2>
            <div className="mt-3 grid gap-2 text-sm text-slate-700">
              <p>张三 13800000000</p>
              <p>北京市朝阳区测试路 1 号</p>
            </div>
          </section>

          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            {selectedItems.map((item) => (
              <article className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[88px_1fr_120px]" key={item.id}>
                <div
                  aria-label={item.product.title}
                  className="aspect-square rounded-md bg-cover bg-center"
                  role="img"
                  style={{ backgroundImage: `url(${item.product.image})` }}
                />
                <div>
                  <h2 className="font-semibold">{item.product.title}</h2>
                  <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                  <p className="mt-2 text-xs text-slate-500">结算时已重算价格、库存和商品可售状态</p>
                </div>
                <div className="text-sm font-semibold">
                  <p>{formatPrice(item.sku.price)}</p>
                  <p className="mt-1 text-slate-500">x {item.quantity}</p>
                </div>
              </article>
            ))}
          </section>
        </div>

        <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-base font-semibold">订单金额</h2>
          <div className="mt-4 flex flex-col gap-3 border-b border-slate-100 pb-4 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-600">商品金额</span>
              <span>{formatPrice(selectedCartTotal())}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">运费</span>
              <span>{formatPrice(0)}</span>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <span className="text-sm text-slate-600">应付</span>
            <span className="text-2xl font-semibold text-commerce-red">{formatPrice(selectedCartTotal())}</span>
          </div>
          <Link
            className="mt-5 block rounded-md bg-commerce-red px-5 py-3 text-center text-sm font-semibold text-white"
            href="/orders/order-20260716002"
          >
            提交订单
          </Link>
        </aside>
      </section>
    </main>
  );
}
