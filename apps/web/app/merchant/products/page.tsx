import Link from "next/link";

import { availableStock, demoProducts, formatPrice } from "@/lib/catalog-demo";

const statusCopy = {
  draft: "草稿",
  published: "已上架",
  unpublished: "已下架"
};

export default function MerchantProductsPage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-teal">商家后台</p>
            <h1 className="mt-1 text-2xl font-semibold">商品与库存管理</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/merchant/login">
            商家登录
          </Link>
        </header>

        <div className="grid gap-4 md:grid-cols-4">
          {[
            ["商品数", demoProducts.length],
            ["已上架", demoProducts.filter((item) => item.status === "published").length],
            ["库存预警", demoProducts.filter((item) => item.stockRisk !== "充足").length],
            ["可售库存", demoProducts.reduce((total, item) => total + availableStock(item), 0)]
          ].map(([label, value]) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={label}>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>

        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="grid grid-cols-[1.6fr_0.8fr_0.8fr_0.8fr_1fr] border-b border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">
            <span>商品</span>
            <span>状态</span>
            <span>价格</span>
            <span>可售</span>
            <span>操作</span>
          </div>
          {demoProducts.map((product) => (
            <div className="grid min-h-24 grid-cols-[1.6fr_0.8fr_0.8fr_0.8fr_1fr] items-center border-b border-slate-100 px-4 py-3 text-sm last:border-b-0" key={product.id}>
              <div>
                <p className="font-semibold">{product.title}</p>
                <p className="mt-1 text-slate-500">{product.category} / {product.brand}</p>
              </div>
              <span>{statusCopy[product.status]}</span>
              <span className="font-semibold">{formatPrice(product.price)}</span>
              <span className={product.stockRisk === "充足" ? "text-commerce-teal" : "text-commerce-red"}>
                {availableStock(product)} / {product.stockRisk}
              </span>
              <div className="flex flex-wrap gap-2">
                <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                  编辑
                </button>
                <button className="rounded-md border border-slate-300 px-3 py-2 font-semibold" type="button">
                  调库存
                </button>
                <button className="rounded-md bg-commerce-ink px-3 py-2 font-semibold text-white" type="button">
                  {product.status === "published" ? "下架" : "上架"}
                </button>
              </div>
            </div>
          ))}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-base font-semibold">库存调整队列</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {demoProducts.flatMap((product) =>
              product.skus.map((sku) => (
                <div className="rounded-md border border-slate-200 p-3" key={sku.code}>
                  <p className="font-medium">{product.title}</p>
                  <p className="mt-1 text-sm text-slate-500">{sku.spec}</p>
                  <p className="mt-2 text-sm">
                    现货 {sku.stock}，已预留 {sku.reserved}，可售 {Math.max(0, sku.stock - sku.reserved)}
                  </p>
                </div>
              ))
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
