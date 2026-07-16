import Link from "next/link";

import { formatPrice } from "@/lib/catalog-demo";
import { demoOrders, orderTotal } from "@/lib/order-demo";

export default function OrdersPage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-red">我的订单</p>
            <h1 className="mt-1 text-2xl font-semibold">订单列表</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/cart">
            查看购物车
          </Link>
        </header>

        <div className="flex flex-col gap-4">
          {demoOrders.map((order) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={order.id}>
              <div className="flex flex-col gap-2 border-b border-slate-100 pb-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold">{order.orderNo}</p>
                  <p className="mt-1 text-xs text-slate-500">{order.createdAt}</p>
                </div>
                <span className="w-fit rounded-md bg-slate-100 px-3 py-1 text-sm font-semibold text-commerce-ink">
                  {order.statusText}
                </span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-[1fr_140px_120px] md:items-center">
                <div className="flex flex-col gap-2">
                  {order.items.map((item) => (
                    <p className="text-sm text-slate-700" key={item.sku.code}>
                      {item.product.title} / {item.sku.spec} x {item.quantity}
                    </p>
                  ))}
                </div>
                <p className="font-semibold text-commerce-red">{formatPrice(orderTotal(order))}</p>
                <Link
                  className="rounded-md border border-commerce-teal px-3 py-2 text-center text-sm font-semibold text-commerce-teal"
                  href={`/orders/${order.id}`}
                >
                  查看详情
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
