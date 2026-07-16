import Link from "next/link";
import { notFound } from "next/navigation";

import { demoAfterSales } from "@/lib/after-sales-demo";
import { formatPrice } from "@/lib/catalog-demo";

type AfterSalesDetailPageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return demoAfterSales.map((item) => ({ id: item.id }));
}

export default async function AfterSalesDetailPage({ params }: AfterSalesDetailPageProps) {
  const { id } = await params;
  const item = demoAfterSales.find((entry) => entry.id === id);
  if (!item) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto grid max-w-6xl gap-5 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-5">
          <header className="flex flex-col gap-3 border-b border-slate-200 pb-5">
            <Link className="text-sm font-semibold text-commerce-teal" href="/after-sales">
              返回售后列表
            </Link>
            <div>
              <p className="text-sm font-semibold text-commerce-red">{item.no}</p>
              <h1 className="mt-1 text-2xl font-semibold">{item.statusText}</h1>
            </div>
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">售后时间线</h2>
            <div className="mt-4 grid gap-3">
              {item.timeline.map((event) => (
                <div className="grid grid-cols-[80px_1fr] gap-3 text-sm" key={event.label}>
                  <p className="font-semibold text-commerce-red">{event.time}</p>
                  <p>{event.label}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">用户诉求与凭证</h2>
            <p className="mt-3 text-sm leading-6 text-slate-700">{item.customerNote}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button">
                补充凭证
              </button>
              <button className="rounded-md border border-commerce-red px-3 py-2 text-sm font-semibold text-commerce-red" type="button">
                申请客服介入
              </button>
            </div>
          </section>
        </div>

        <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-base font-semibold">售后摘要</h2>
          <div className="mt-4 flex flex-col gap-2 text-sm text-slate-700">
            <p>{item.item.product.title}</p>
            <p>{item.item.sku.spec}</p>
            <p>{item.merchant}</p>
            <p>处理时限：{item.deadline}</p>
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
            <span className="text-sm text-slate-600">退款金额</span>
            <span className="text-2xl font-semibold text-commerce-red">{formatPrice(item.refundAmount)}</span>
          </div>
        </aside>
      </section>
    </main>
  );
}
