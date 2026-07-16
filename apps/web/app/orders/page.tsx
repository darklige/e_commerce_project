import Link from "next/link";
import { Clock3, CreditCard, PackageCheck, Search, Truck } from "lucide-react";

import { PageHeader, StatusPill, UserCommerceShell } from "@/components/user-commerce";
import { formatPrice } from "@/lib/catalog-demo";
import { demoOrders, orderTotal } from "@/lib/order-demo";

function orderTone(status: string) {
  if (status === "pending_payment") return "gold" as const;
  if (status === "paid_pending_shipment") return "teal" as const;
  return "slate" as const;
}

export default function OrdersPage() {
  return (
    <UserCommerceShell active="orders">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow="我的订单"
          title="订单列表"
          description="集中查看支付倒计时、履约状态、订单快照和售后入口，用户不需要猜下一步该做什么。"
          action={
            <Link className="rounded-md bg-commerce-red px-4 py-2 text-sm font-bold text-white" href="/products">
              继续购物
            </Link>
          }
        />

        <div className="grid gap-3 md:grid-cols-4">
          {[
            { label: "待支付", value: "1", icon: CreditCard },
            { label: "待发货", value: "1", icon: Truck },
            { label: "售后中", value: "4", icon: PackageCheck },
            { label: "提醒", value: "2", icon: Clock3 }
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
            <input className="h-11 w-full rounded-md border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-commerce-red" placeholder="搜索订单号、商品名称或售后状态" />
          </label>
          <button className="rounded-md bg-commerce-ink px-4 text-sm font-bold text-white" type="button">
            查询
          </button>
        </form>

        <div className="grid gap-4">
          {demoOrders.map((order) => (
            <article className="overflow-hidden rounded-md border border-slate-200 bg-white" key={order.id}>
              <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-black">{order.orderNo}</p>
                  <p className="mt-1 text-xs text-slate-500">下单时间 {order.createdAt}</p>
                </div>
                <StatusPill tone={orderTone(order.status)}>{order.statusText}</StatusPill>
              </div>
              <div className="grid gap-4 p-4 lg:grid-cols-[1fr_180px_150px] lg:items-center">
                <div className="grid gap-3">
                  {order.items.map((item) => (
                    <div className="grid grid-cols-[72px_1fr] gap-3" key={item.sku.code}>
                      <div
                        aria-label={item.product.title}
                        className="aspect-square rounded-md bg-cover bg-center"
                        role="img"
                        style={{ backgroundImage: `url(${item.product.image})` }}
                      />
                      <div>
                        <p className="font-bold">{item.product.title}</p>
                        <p className="mt-1 text-sm text-slate-500">{item.sku.spec} x {item.quantity}</p>
                        <p className="mt-2 text-xs text-commerce-teal">订单快照已保存</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs text-slate-500">实付金额</p>
                  <p className="mt-1 text-xl font-black text-commerce-red">{formatPrice(orderTotal(order))}</p>
                </div>
                <div className="grid gap-2">
                  <Link
                    className="rounded-md bg-commerce-red px-3 py-2 text-center text-sm font-bold text-white"
                    href={`/orders/${order.id}`}
                  >
                    查看详情
                  </Link>
                  <Link
                    className="rounded-md border border-slate-200 px-3 py-2 text-center text-sm font-bold"
                    href={order.status === "pending_payment" ? `/orders/${order.id}` : "/after-sales"}
                  >
                    {order.status === "pending_payment" ? "去支付" : "申请售后"}
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </UserCommerceShell>
  );
}
