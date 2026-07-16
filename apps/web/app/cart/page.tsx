import Link from "next/link";
import { AlertTriangle, Minus, Plus, ShieldCheck, ShoppingBag, Trash2 } from "lucide-react";

import { PageHeader, StatusPill, UserCommerceShell } from "@/components/user-commerce";
import { availableStock, formatPrice } from "@/lib/catalog-demo";
import { cartLineTotal, demoCartItems, selectedCartCount, selectedCartTotal } from "@/lib/order-demo";

export default function CartPage() {
  return (
    <UserCommerceShell active="cart">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow="购物车"
          title="已选商品"
          description="模拟购物车会展示库存风险、选中状态和结算金额，进入结算时会再次校验价格与库存。"
          action={
            <Link className="rounded-md bg-commerce-ink px-4 py-2 text-sm font-bold text-white" href="/products">
              继续购物
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
            <div className="grid grid-cols-[32px_1fr_120px_120px_120px] gap-4 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-bold text-slate-500 max-md:hidden">
              <span />
              <span>商品信息</span>
              <span>单价</span>
              <span>数量</span>
              <span>小计</span>
            </div>
            {demoCartItems.map((item) => {
              const available = Math.max(0, item.sku.stock - item.sku.reserved);
              const blocked = available < item.quantity || item.product.status !== "published";
              return (
                <article
                  className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[32px_112px_1fr_120px_120px_120px] md:items-center"
                  key={item.id}
                >
                  <input aria-label={item.product.title} checked={item.selected} readOnly type="checkbox" className="h-4 w-4 accent-commerce-red" />
                  <div
                    aria-label={item.product.title}
                    className="aspect-square rounded-md bg-cover bg-center"
                    role="img"
                    style={{ backgroundImage: `url(${item.product.image})` }}
                  />
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-black">{item.product.title}</h2>
                      {blocked ? <StatusPill tone="red">库存风险</StatusPill> : <StatusPill tone="teal">可结算</StatusPill>}
                    </div>
                    <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                    <p className={blocked ? "mt-2 flex items-center gap-1 text-sm font-semibold text-commerce-red" : "mt-2 text-sm font-semibold text-commerce-teal"}>
                      {blocked ? <AlertTriangle className="h-4 w-4" aria-hidden="true" /> : null}
                      可售 {availableStock(item.product)}，当前规格可售 {available}
                    </p>
                  </div>
                  <div className="text-sm">
                    <p className="font-bold">{formatPrice(item.sku.price)}</p>
                    <p className="mt-1 text-xs text-slate-500">价保中</p>
                  </div>
                  <div className="flex h-10 w-fit items-center overflow-hidden rounded-md border border-slate-200">
                    <button className="flex h-10 w-10 items-center justify-center text-slate-500" type="button" aria-label="减少数量">
                      <Minus className="h-4 w-4" aria-hidden="true" />
                    </button>
                    <span className="flex h-10 w-10 items-center justify-center border-x border-slate-200 text-sm font-bold">{item.quantity}</span>
                    <button className="flex h-10 w-10 items-center justify-center text-slate-500" type="button" aria-label="增加数量">
                      <Plus className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-base font-black text-commerce-red">{formatPrice(cartLineTotal(item))}</p>
                    <button className="text-slate-400 transition hover:text-commerce-red" type="button" aria-label="删除商品">
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                </article>
              );
            })}
          </section>

          <aside className="h-fit rounded-md border border-slate-200 bg-white p-5">
            <h2 className="flex items-center gap-2 text-lg font-black">
              <ShoppingBag className="h-5 w-5 text-commerce-red" aria-hidden="true" />
              结算摘要
            </h2>
            <div className="mt-5 grid gap-3 border-b border-slate-100 pb-4 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">已选商品</span>
                <span className="font-bold">{selectedCartCount()} 件</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">商品金额</span>
                <span className="font-bold">{formatPrice(selectedCartTotal())}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">预计运费</span>
                <span className="font-bold">{formatPrice(0)}</span>
              </div>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <span className="text-sm text-slate-500">应付合计</span>
              <span className="text-3xl font-black text-commerce-red">{formatPrice(selectedCartTotal())}</span>
            </div>
            <Link
              className="mt-5 flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-5 text-sm font-bold text-white"
              href="/checkout"
            >
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              去结算
            </Link>
            <p className="mt-3 text-xs leading-5 text-slate-500">提交订单前会再次校验商品、价格、库存、地址可配送性。</p>
          </aside>
        </div>
      </section>
    </UserCommerceShell>
  );
}
