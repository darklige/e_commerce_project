import Link from "next/link";
import { notFound } from "next/navigation";
import { BadgeCheck, ChevronLeft, Heart, PackageCheck, ShieldCheck, ShoppingCart, Truck, Zap } from "lucide-react";

import { PageHeader, QuickIconLink, StatusPill, UserCommerceShell } from "@/components/user-commerce";
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
    <UserCommerceShell active="products">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow={`${product.category} / ${product.brand}`}
          title={product.title}
          description={product.subtitle}
          action={
            <div className="flex flex-wrap gap-2">
              <QuickIconLink href="/products" label="返回列表" icon={ChevronLeft} />
              <QuickIconLink href="/cart" label="购物车" icon={ShoppingCart} />
            </div>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[minmax(0,520px)_1fr]">
          <section className="grid gap-3">
            <div
              aria-label={product.title}
              className="aspect-square rounded-md border border-slate-200 bg-cover bg-center"
              role="img"
              style={{ backgroundImage: `url(${product.image})` }}
            />
            <div className="grid grid-cols-4 gap-2">
              {product.skus.map((sku) => (
                <div className="rounded-md border border-slate-200 bg-white p-2 text-xs font-semibold" key={sku.code}>
                  {sku.spec}
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-4">
            <div className="rounded-md border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap gap-2">
                <StatusPill tone="red">官方自营</StatusPill>
                <StatusPill tone="teal">极速发货</StatusPill>
                <StatusPill tone="gold">价保服务</StatusPill>
              </div>
              <div className="mt-5 flex flex-col gap-4 border-b border-slate-100 pb-5 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-500">到手价</p>
                  <p className="mt-1 text-4xl font-black text-commerce-red">{formatPrice(product.price)}</p>
                </div>
                <p className="rounded-md bg-red-50 px-3 py-2 text-sm font-bold text-commerce-red">
                  当前商品总可售库存 {availableStock(product)}
                </p>
              </div>

              <div className="mt-5 grid gap-4">
                <div>
                  <p className="text-sm font-bold">选择规格</p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {product.skus.map((sku, index) => {
                      const available = Math.max(0, sku.stock - sku.reserved);
                      return (
                        <button
                          className={
                            index === 0
                              ? "rounded-md border-2 border-commerce-red bg-red-50 p-3 text-left"
                              : "rounded-md border border-slate-200 bg-white p-3 text-left"
                          }
                          key={sku.code}
                          type="button"
                        >
                          <span className="block text-sm font-bold">{sku.spec}</span>
                          <span className="mt-1 block text-xs text-slate-500">{formatPrice(sku.price)} / 可售 {available}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid gap-3 rounded-md bg-slate-50 p-4 md:grid-cols-3">
                  {[
                    { icon: Truck, label: "配送", value: "北京核心区极速达" },
                    { icon: ShieldCheck, label: "保障", value: "正品与价保" },
                    { icon: PackageCheck, label: "售后", value: "支持退货退款" }
                  ].map((item) => {
                    const Icon = item.icon;
                    return (
                      <div className="flex gap-3" key={item.label}>
                        <Icon className="mt-0.5 h-5 w-5 text-commerce-red" aria-hidden="true" />
                        <div>
                          <p className="text-sm font-bold">{item.label}</p>
                          <p className="mt-1 text-xs leading-5 text-slate-500">{item.value}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="grid gap-3 sm:grid-cols-[1fr_1fr_48px]">
                  <Link className="flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-4 text-sm font-bold text-white" href="/cart">
                    <ShoppingCart className="h-4 w-4" aria-hidden="true" />
                    加入购物车
                  </Link>
                  <Link className="flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-ink px-4 text-sm font-bold text-white" href="/checkout">
                    <Zap className="h-4 w-4" aria-hidden="true" />
                    立即结算
                  </Link>
                  <button className="flex h-12 items-center justify-center rounded-md border border-slate-200 bg-white text-commerce-red" type="button" aria-label="收藏商品">
                    <Heart className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>

            <section className="rounded-md border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-black">SKU 规格与库存</h2>
              <div className="mt-4 grid gap-3">
                {product.skus.map((sku) => {
                  const available = Math.max(0, sku.stock - sku.reserved);
                  return (
                    <div className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_140px_120px]" key={sku.code}>
                      <div>
                        <p className="font-bold">{sku.spec}</p>
                        <p className="mt-1 text-xs text-slate-500">{sku.code}</p>
                      </div>
                      <p className="text-sm font-bold">{formatPrice(sku.price)}</p>
                      <p className={available > 0 ? "text-sm font-bold text-commerce-teal" : "text-sm font-bold text-commerce-red"}>
                        可售 {available}
                      </p>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-5">
              <h2 className="flex items-center gap-2 text-lg font-black">
                <BadgeCheck className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                购买说明
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                结算时会重新校验价格、库存、商品上架状态和地址配送能力。库存不足或商品下架时，下单会被阻止并提示用户重新选择。
              </p>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                演示链路保留模拟支付与售后状态机，用于验证订单、库存、售后和客服介入的联动体验。
              </p>
            </section>
          </section>
        </div>

        <section className="grid gap-4">
          <div>
            <p className="text-sm font-bold text-commerce-red">同类推荐</p>
            <h2 className="mt-1 text-2xl font-black">你可能还喜欢</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {demoProducts
              .filter((item) => item.status === "published" && item.id !== product.id)
              .map((item) => (
                <Link className="rounded-md border border-slate-200 bg-white p-4" href={`/products/${item.id}`} key={item.id}>
                  <p className="text-sm font-bold">{item.title}</p>
                  <p className="mt-1 text-sm text-slate-500">{item.subtitle}</p>
                  <p className="mt-3 text-lg font-black text-commerce-red">{formatPrice(item.price)}</p>
                </Link>
              ))}
          </div>
        </section>
      </section>
    </UserCommerceShell>
  );
}
