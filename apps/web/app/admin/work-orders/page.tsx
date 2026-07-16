import Link from "next/link";

import { demoWorkOrders } from "@/lib/after-sales-demo";
import { formatPrice } from "@/lib/catalog-demo";

export default function AdminWorkOrdersPage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-gold">管理员客服</p>
            <h1 className="mt-1 text-2xl font-semibold">售后工单工作台</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/admin/login">
            管理员入口
          </Link>
        </header>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ["待处理工单", "2"],
            ["退款异常", "1"],
            ["商家超时风险", "1"]
          ].map(([label, value]) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={label}>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </section>

        <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <div className="min-w-[1040px]">
            <div className="grid grid-cols-[1.05fr_0.7fr_0.55fr_0.9fr_1.4fr_1fr_1fr] border-b border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">
              <span>工单</span>
              <span>队列</span>
              <span>优先级</span>
              <span>关联售后</span>
              <span>证据链</span>
              <span>内部备注</span>
              <span>处理</span>
            </div>
            {demoWorkOrders.map((workOrder) => (
              <div className="grid min-h-32 grid-cols-[1.05fr_0.7fr_0.55fr_0.9fr_1.4fr_1fr_1fr] items-center border-b border-slate-100 px-4 py-3 text-sm last:border-b-0" key={workOrder.id}>
                <div>
                  <p className="font-semibold">{workOrder.no}</p>
                  <p className="mt-1 text-slate-500">{workOrder.reason}</p>
                </div>
                <p>{workOrder.queue}</p>
                <p className="font-semibold text-commerce-red">{workOrder.priority}</p>
                <div>
                  <p>{workOrder.afterSales.no}</p>
                  <p className="mt-1 text-commerce-red">{formatPrice(workOrder.afterSales.refundAmount)}</p>
                </div>
                <p className="pr-4 leading-6 text-slate-600">{workOrder.evidenceSummary}</p>
                <p className="pr-4 leading-6 text-slate-600">{workOrder.internalNotes}</p>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-commerce-teal px-3 py-2 font-semibold text-commerce-teal" type="button">
                    裁定退款
                  </button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                    要求补证
                  </button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                    驳回
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
