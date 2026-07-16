import Link from "next/link";
import { notFound } from "next/navigation";

import { availableStock, demoProducts, formatPrice } from "@/lib/catalog-demo";

type ProductDetailPageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return demoProducts.map((product) => ({ id: product.id }));
}

export default async function ProductDetailPage({ params }: ProductDetailPageProps) {
  const { id } = await params;
  const product = demoProducts.find((item) => item.id === id && item.status === "published");
  if (!product) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[minmax(0,480px)_1fr]">
        <div
          aria-label={product.title}
          className="aspect-square w-full rounded-lg bg-cover bg-center"
          role="img"
          style={{ backgroundImage: `url(${product.image})` }}
        />
        <div className="flex flex-col gap-5">
          <div className="border-b border-slate-200 pb-5">
            <Link className="text-sm font-semibold text-commerce-teal" href="/products">
              返回商品列表
            </Link>
            <p className="mt-4 text-sm font-semibold text-slate-500">
              {product.category} / {product.brand}
            </p>
            <h1 className="mt-2 text-3xl font-semibold">{product.title}</h1>
            <p className="mt-3 text-base leading-7 text-slate-600">{product.subtitle}</p>
            <p className="mt-4 text-2xl font-semibold text-commerce-red">{formatPrice(product.price)}</p>
          </div>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-base font-semibold">SKU 规格与库存</h2>
            <div className="mt-4 flex flex-col gap-3">
              {product.skus.map((sku) => {
                const available = Math.max(0, sku.stock - sku.reserved);
                return (
                  <div className="grid gap-2 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_120px_120px]" key={sku.code}>
                    <div>
                      <p className="font-medium">{sku.spec}</p>
                      <p className="text-xs text-slate-500">{sku.code}</p>
                    </div>
                    <p className="text-sm font-semibold">{formatPrice(sku.price)}</p>
                    <p className={available > 0 ? "text-sm text-commerce-teal" : "text-sm text-commerce-red"}>
                      可售 {available}
                    </p>
                  </div>
                );
              })}
            </div>
          </section>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-sm text-slate-600">
              当前商品总可售库存 {availableStock(product)}。库存不足或商品下架时，结算流程会重新校验价格和库存。
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
