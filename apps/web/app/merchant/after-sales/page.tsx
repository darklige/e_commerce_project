import Link from "next/link";

import { demoAfterSales } from "@/lib/after-sales-demo";
import { formatPrice } from "@/lib/catalog-demo";

export default function MerchantAfterSalesPage() {
  const queue = demoAfterSales.filter((item) => item.status !== "refunded");

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-teal">商家售后</p>
            <h1 className="mt-1 text-2xl font-semibold">售后处理队列</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/merchant/products">
            商品管理
          </Link>
        </header>

        <section className="grid gap-3 md:grid-cols-4">
          {[
            ["待审核", "1"],
            ["待收货", "1"],
            ["退款异常", "1"],
            ["高风险", "2"]
          ].map(([label, value]) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={label}>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </section>

        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="grid grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_1fr] border-b border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">
            <span>售后单</span>
            <span>状态</span>
            <span>时限</span>
            <span>金额</span>
            <span>操作</span>
          </div>
          {queue.map((item) => (
            <div className="grid min-h-24 grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr_1fr] items-center border-b border-slate-100 px-4 py-3 text-sm last:border-b-0" key={item.id}>
              <div>
                <p className="font-semibold">{item.no}</p>
                <p className="mt-1 text-slate-500">{item.reason}</p>
              </div>
              <p>{item.statusText}</p>
              <p className={item.risk === "高" ? "font-semibold text-commerce-red" : "text-slate-600"}>{item.deadline}</p>
              <p className="font-semibold">{formatPrice(item.refundAmount)}</p>
              <div className="flex flex-wrap gap-2">
                <button className="rounded-md border border-commerce-teal px-3 py-2 font-semibold text-commerce-teal" type="button">
                  同意
                </button>
                <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                  拒绝
                </button>
                <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                  查看
                </button>
              </div>
            </div>
          ))}
        </section>
      </section>
    </main>
  );
}
