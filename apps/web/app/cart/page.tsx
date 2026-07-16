import Link from "next/link";

import { availableStock, formatPrice } from "@/lib/catalog-demo";
import { cartLineTotal, demoCartItems, selectedCartCount, selectedCartTotal } from "@/lib/order-demo";

export default function CartPage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-red">购物车</p>
            <h1 className="mt-1 text-2xl font-semibold">已选商品</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/products">
            继续购物
          </Link>
        </header>

        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          {demoCartItems.map((item) => {
            const available = Math.max(0, item.sku.stock - item.sku.reserved);
            const blocked = available < item.quantity || item.product.status !== "published";
            return (
              <article
                className="grid gap-4 border-b border-slate-100 p-4 last:border-b-0 md:grid-cols-[32px_112px_1fr_140px_120px]"
                key={item.id}
              >
                <input aria-label={item.product.title} checked={item.selected} readOnly type="checkbox" />
                <div
                  aria-label={item.product.title}
                  className="aspect-square rounded-md bg-cover bg-center"
                  role="img"
                  style={{ backgroundImage: `url(${item.product.image})` }}
                />
                <div>
                  <h2 className="font-semibold">{item.product.title}</h2>
                  <p className="mt-1 text-sm text-slate-600">{item.sku.spec}</p>
                  <p className={blocked ? "mt-2 text-sm text-commerce-red" : "mt-2 text-sm text-commerce-teal"}>
                    可售 {availableStock(item.product)}，当前规格可售 {available}
                  </p>
                </div>
                <div className="text-sm">
                  <p className="font-semibold">{formatPrice(item.sku.price)}</p>
                  <p className="mt-2 text-slate-500">数量 {item.quantity}</p>
                </div>
                <p className="text-base font-semibold text-commerce-red">{formatPrice(cartLineTotal(item))}</p>
              </article>
            );
          })}
        </section>

        <footer className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm text-slate-600">已选 {selectedCartCount()} 件</p>
            <p className="text-xl font-semibold text-commerce-red">{formatPrice(selectedCartTotal())}</p>
          </div>
          <Link
            className="rounded-md bg-commerce-red px-5 py-3 text-center text-sm font-semibold text-white"
            href="/checkout"
          >
            去结算
          </Link>
        </footer>
      </section>
    </main>
  );
}
