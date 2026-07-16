import Link from "next/link";
import { notFound } from "next/navigation";
import { CreditCard, MapPin, PackageCheck, RefreshCw, ShieldCheck, Truck } from "lucide-react";

import { PageHeader, StatusPill, Timeline, UserCommerceShell } from "@/components/user-commerce";
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

  const pendingPayment = order.status === "pending_payment";

  return (
    <UserCommerceShell active="orders">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow={order.orderNo}
          title={order.statusText}
          description={pendingPayment ? "请在支付倒计时内完成模拟支付，超时后订单会关闭并释放库存。" : "订单已支付，等待商家发货；如商品存在问题，可从这里进入售后流程。"}
          action={
            <Link className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-bold" href="/orders">
              返回订单列表
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
          <div className="grid gap-5">
            <section className="rounded-md border border-slate-200 bg-white p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <h2 className="flex items-center gap-2 text-lg font-black">
                  <Truck className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                  订单进度
                </h2>
                <StatusPill tone={pendingPayment ? "gold" : "teal"}>{pendingPayment ? "待模拟支付" : "商家处理中"}</StatusPill>
              </div>
              <div className="mt-5">
                <Timeline steps={order.timeline} />
              </div>
            </section>

            <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
              <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
                <h2 className="text-lg font-black">商品快照</h2>
                <p className="text-xs font-semibold text-slate-500">价格、规格、地址已固化</p>
              </div>
              {order.items.map((item) => (
                <article className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[88px_1fr_120px]" key={item.sku.code}>
                  <div
                    aria-label={item.product.title}
                    className="aspect-square rounded-md bg-cover bg-center"
                    role="img"
                    style={{ backgroundImage: `url(${item.product.image})` }}
                  />
                  <div>
                    <h3 className="font-black">{item.product.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                    <p className="mt-2 text-xs text-slate-500">如需退款或退货，可从右侧操作区申请售后。</p>
                  </div>
                  <p className="text-sm font-bold">
                    {formatPrice(item.paidPrice)} x {item.quantity}
                  </p>
                </article>
              ))}
            </section>

            <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-5 md:grid-cols-3">
              {[
                { icon: MapPin, label: "收货人", value: `${order.receiver} ${order.phone}` },
                { icon: ShieldCheck, label: "地址", value: order.address },
                { icon: RefreshCw, label: "状态刷新", value: "支付回跳后可主动刷新订单" }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div className="rounded-md bg-slate-50 p-4" key={item.label}>
                    <Icon className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                    <p className="mt-3 text-sm font-black">{item.label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.value}</p>
                  </div>
                );
              })}
            </section>
          </div>

          <aside className="h-fit rounded-md border border-slate-200 bg-white p-5">
            <h2 className="flex items-center gap-2 text-lg font-black">
              <CreditCard className="h-5 w-5 text-commerce-red" aria-hidden="true" />
              收货与支付
            </h2>
            <div className="mt-4 grid gap-2 text-sm text-slate-700">
              <p className="font-bold">{order.receiver} {order.phone}</p>
              <p>{order.address}</p>
              <p>支付截止 {order.expiresAt}</p>
            </div>
            <div className="mt-5 flex items-end justify-between border-t border-slate-100 pt-4">
              <span className="text-sm text-slate-600">实付</span>
              <span className="text-3xl font-black text-commerce-red">{formatPrice(orderTotal(order))}</span>
            </div>
            {pendingPayment ? (
              <Link
                className="mt-5 flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-5 text-sm font-bold text-white"
                href="/orders/order-20260716001"
              >
                <CreditCard className="h-4 w-4" aria-hidden="true" />
                模拟支付
              </Link>
            ) : (
              <div className="mt-5 grid gap-3">
                <Link
                  className="flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-5 text-sm font-bold text-white"
                  href="/after-sales"
                >
                  <PackageCheck className="h-4 w-4" aria-hidden="true" />
                  申请售后
                </Link>
                <Link
                  className="rounded-md border border-slate-200 px-5 py-3 text-center text-sm font-bold"
                  href="/products"
                >
                  再逛逛
                </Link>
              </div>
            )}
            <p className="mt-4 text-xs leading-5 text-slate-500">敏感操作会写入审计日志，并同步订单、售后和库存状态。</p>
          </aside>
        </div>
      </section>
    </UserCommerceShell>
  );
}
