import Link from "next/link";
import { notFound } from "next/navigation";
import { FilePlus2, Headphones, MessageSquareText, PackageCheck, ShieldCheck } from "lucide-react";

import { PageHeader, StatusPill, Timeline, UserCommerceShell } from "@/components/user-commerce";
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
    <UserCommerceShell active="after-sales">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow={item.no}
          title={item.statusText}
          description="围绕用户诉求、商家处理、客服介入和退款状态展示完整时间线，降低售后过程中的不确定感。"
          action={
            <Link className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-bold" href="/after-sales">
              返回售后列表
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
          <div className="grid gap-5">
            <section className="rounded-md border border-slate-200 bg-white p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <h2 className="flex items-center gap-2 text-lg font-black">
                  <PackageCheck className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                  售后时间线
                </h2>
                <StatusPill tone={item.risk === "高" ? "red" : "gold"}>处理时限：{item.deadline}</StatusPill>
              </div>
              <div className="mt-5">
                <Timeline steps={item.timeline.map((event, index) => ({ ...event, tone: index === item.timeline.length - 1 ? "current" : "done" }))} />
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-5">
              <h2 className="flex items-center gap-2 text-lg font-black">
                <MessageSquareText className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                用户诉求与凭证
              </h2>
              <div className="mt-4 rounded-md bg-slate-50 p-4">
                <p className="text-sm leading-7 text-slate-700">{item.customerNote}</p>
                <p className="mt-3 text-sm font-semibold text-commerce-teal">{item.nextAction}</p>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button className="flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-bold" type="button">
                  <FilePlus2 className="h-4 w-4" aria-hidden="true" />
                  补充凭证
                </button>
                <button className="flex h-10 items-center gap-2 rounded-md border border-commerce-red px-3 text-sm font-bold text-commerce-red" type="button">
                  <Headphones className="h-4 w-4" aria-hidden="true" />
                  申请客服介入
                </button>
              </div>
            </section>

            <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-5 md:grid-cols-3">
              {[
                { label: "商家处理", value: "同意、拒绝或确认收货都需要理由与审计", icon: PackageCheck },
                { label: "平台客服", value: "争议升级后查看证据链并裁定", icon: Headphones },
                { label: "退款安全", value: "退款失败进入财务重试或人工处理", icon: ShieldCheck }
              ].map((entry) => {
                const Icon = entry.icon;
                return (
                  <div className="rounded-md bg-slate-50 p-4" key={entry.label}>
                    <Icon className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                    <p className="mt-3 text-sm font-black">{entry.label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{entry.value}</p>
                  </div>
                );
              })}
            </section>
          </div>

          <aside className="h-fit rounded-md border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-black">售后摘要</h2>
            <div className="mt-4 grid grid-cols-[76px_1fr] gap-3">
              <div
                aria-label={item.item.product.title}
                className="aspect-square rounded-md bg-cover bg-center"
                role="img"
                style={{ backgroundImage: `url(${item.item.product.image})` }}
              />
              <div>
                <p className="font-bold">{item.item.product.title}</p>
                <p className="mt-1 text-sm text-slate-500">{item.item.sku.spec}</p>
                <p className="mt-2 text-xs text-slate-500">{item.merchant}</p>
              </div>
            </div>
            <div className="mt-5 grid gap-2 border-t border-slate-100 pt-4 text-sm text-slate-700">
              <p>售后类型：{item.typeText}</p>
              <p>处理时限：{item.deadline}</p>
              <p>申请原因：{item.reason}</p>
            </div>
            <div className="mt-5 flex items-end justify-between border-t border-slate-100 pt-4">
              <span className="text-sm text-slate-600">退款金额</span>
              <span className="text-3xl font-black text-commerce-red">{formatPrice(item.refundAmount)}</span>
            </div>
          </aside>
        </div>
      </section>
    </UserCommerceShell>
  );
}
