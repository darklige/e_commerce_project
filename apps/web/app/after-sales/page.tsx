import Link from "next/link";

import { formatPrice } from "@/lib/catalog-demo";
import { demoAfterSales } from "@/lib/after-sales-demo";

export default function AfterSalesPage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-red">我的售后</p>
            <h1 className="mt-1 text-2xl font-semibold">售后进度</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/orders">
            返回订单
          </Link>
        </header>

        <div className="grid gap-4">
          {demoAfterSales.map((item) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={item.id}>
              <div className="flex flex-col gap-2 border-b border-slate-100 pb-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold">{item.no}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.orderNo} / {item.typeText}
                  </p>
                </div>
                <span className="w-fit rounded-md bg-slate-100 px-3 py-1 text-sm font-semibold">
                  {item.statusText}
                </span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-[1fr_140px_140px_112px] md:items-center">
                <div>
                  <p className="text-sm font-semibold">{item.item.product.title}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.reason}</p>
                  <p className="mt-2 text-xs text-commerce-teal">{item.nextAction}</p>
                </div>
                <p className="text-sm text-slate-600">{item.deadline}</p>
                <p className="font-semibold text-commerce-red">{formatPrice(item.refundAmount)}</p>
                <Link
                  className="rounded-md border border-commerce-teal px-3 py-2 text-center text-sm font-semibold text-commerce-teal"
                  href={`/after-sales/${item.id}`}
                >
                  查看
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
