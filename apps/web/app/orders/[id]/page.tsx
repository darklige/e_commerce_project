import Link from "next/link";
import { notFound } from "next/navigation";

import { formatPrice } from "@/lib/catalog-demo";
import { demoOrders, orderTotal } from "@/lib/order-demo";

type OrderDetailPageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return demoOrders.map((order) => ({ id: order.id }));
}

export default async function OrderDetailPage({ params }: OrderDetailPageProps) {
  const { id } = await params;
  const order = demoOrders.find((item) => item.id === id);
  if (!order) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto grid max-w-6xl gap-5 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-5">
          <header className="flex flex-col gap-3 border-b border-slate-200 pb-5">
            <Link className="text-sm font-semibold text-commerce-teal" href="/orders">
              返回订单列表
            </Link>
            <div>
              <p className="text-sm font-semibold text-commerce-red">{order.orderNo}</p>
              <h1 className="mt-1 text-2xl font-semibold">{order.statusText}</h1>
            </div>
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">订单进度</h2>
            <div className="mt-4 grid gap-3">
              {order.timeline.map((event) => (
                <div className="grid grid-cols-[96px_1fr] gap-3 text-sm" key={event.label}>
                  <p className={event.tone === "current" ? "font-semibold text-commerce-red" : "text-slate-500"}>
                    {event.time}
                  </p>
                  <p>{event.label}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            {order.items.map((item) => (
              <article className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[88px_1fr_120px]" key={item.sku.code}>
                <div
                  aria-label={item.product.title}
                  className="aspect-square rounded-md bg-cover bg-center"
                  role="img"
                  style={{ backgroundImage: `url(${item.product.image})` }}
                />
                <div>
                  <h2 className="font-semibold">{item.product.title}</h2>
                  <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                  <p className="mt-2 text-xs text-slate-500">商品价格、规格、收货地址已写入订单快照</p>
                </div>
                <p className="text-sm font-semibold">
                  {formatPrice(item.paidPrice)} x {item.quantity}
                </p>
              </article>
            ))}
          </section>
        </div>

        <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-base font-semibold">收货与支付</h2>
          <div className="mt-4 flex flex-col gap-2 text-sm text-slate-700">
            <p>{order.receiver} {order.phone}</p>
            <p>{order.address}</p>
            <p>支付截止 {order.expiresAt}</p>
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
            <span className="text-sm text-slate-600">实付</span>
            <span className="text-2xl font-semibold text-commerce-red">{formatPrice(orderTotal(order))}</span>
          </div>
          {order.status === "pending_payment" ? (
            <Link
              className="mt-5 block rounded-md bg-commerce-red px-5 py-3 text-center text-sm font-semibold text-white"
              href="/orders/order-20260716001"
            >
              模拟支付
            </Link>
          ) : (
            <div className="mt-5 grid gap-3">
              <Link
                className="block rounded-md bg-commerce-red px-5 py-3 text-center text-sm font-semibold text-white"
                href="/after-sales"
              >
                申请售后
              </Link>
              <Link
                className="block rounded-md border border-commerce-teal px-5 py-3 text-center text-sm font-semibold text-commerce-teal"
                href="/products"
              >
                再逛逛
              </Link>
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}
