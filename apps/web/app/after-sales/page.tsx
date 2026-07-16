import Link from "next/link";
import { AlertTriangle, Clock3, Headphones, PackageCheck, Search } from "lucide-react";

import { PageHeader, StatusPill, UserCommerceShell } from "@/components/user-commerce";
import { formatPrice } from "@/lib/catalog-demo";
import { demoAfterSales } from "@/lib/after-sales-demo";

function riskTone(risk: string) {
  if (risk === "高") return "red" as const;
  if (risk === "中") return "gold" as const;
  return "teal" as const;
}

export default function AfterSalesPage() {
  return (
    <UserCommerceShell active="after-sales">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow="我的售后"
          title="售后进度"
          description="展示商家审核、用户退货、退款失败、客服介入和完成状态，让用户知道下一步由谁处理。"
          action={
            <Link className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-bold" href="/orders">
              返回订单
            </Link>
          }
        />

        <div className="grid gap-3 md:grid-cols-4">
          {[
            { label: "商家待处理", value: "1", icon: Clock3 },
            { label: "待我退货", value: "1", icon: PackageCheck },
            { label: "退款异常", value: "1", icon: AlertTriangle },
            { label: "客服跟进", value: "2", icon: Headphones }
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div className="rounded-md border border-slate-200 bg-white p-4" key={item.label}>
                <Icon className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                <p className="mt-3 text-sm text-slate-500">{item.label}</p>
                <p className="mt-1 text-2xl font-black">{item.value}</p>
              </div>
            );
          })}
        </div>

        <form className="grid gap-3 rounded-md border border-slate-200 bg-white p-4 md:grid-cols-[1fr_140px]">
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input className="h-11 w-full rounded-md border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-commerce-red" placeholder="搜索售后单号、订单号、处理状态" />
          </label>
          <button className="rounded-md bg-commerce-ink px-4 text-sm font-bold text-white" type="button">
            查询
          </button>
        </form>

        <div className="grid gap-4">
          {demoAfterSales.map((item) => (
            <article className="overflow-hidden rounded-md border border-slate-200 bg-white" key={item.id}>
              <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-black">{item.no}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.orderNo} / {item.typeText}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusPill tone={riskTone(item.risk)}>风险 {item.risk}</StatusPill>
                  <StatusPill tone="slate">{item.statusText}</StatusPill>
                </div>
              </div>
              <div className="grid gap-4 p-4 lg:grid-cols-[1fr_160px_160px_120px] lg:items-center">
                <div className="grid grid-cols-[72px_1fr] gap-3">
                  <div
                    aria-label={item.item.product.title}
                    className="aspect-square rounded-md bg-cover bg-center"
                    role="img"
                    style={{ backgroundImage: `url(${item.item.product.image})` }}
                  />
                  <div>
                    <p className="font-black">{item.item.product.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{item.reason}</p>
                    <p className="mt-2 text-xs font-semibold text-commerce-teal">{item.nextAction}</p>
                  </div>
                </div>
                <p className="text-sm text-slate-600">{item.deadline}</p>
                <p className="text-xl font-black text-commerce-red">{formatPrice(item.refundAmount)}</p>
                <Link
                  className="rounded-md bg-commerce-red px-3 py-2 text-center text-sm font-bold text-white"
                  href={`/after-sales/${item.id}`}
                >
                  查看
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </UserCommerceShell>
  );
}
