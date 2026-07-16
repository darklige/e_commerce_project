import Link from "next/link";
import { Filter, SlidersHorizontal } from "lucide-react";

import { PageHeader, ProductCard, StatusPill, UserCommerceShell } from "@/components/user-commerce";
import { demoProducts } from "@/lib/catalog-demo";

type ProductsPageProps = {
  searchParams?: Promise<{
    q?: string;
    category?: string;
  }>;
};

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = (await searchParams) ?? {};
  const query = params.q?.trim().toLowerCase() ?? "";
  const category = params.category ?? "all";
  const products = demoProducts.filter((product) => {
    const matchesQuery =
      !query ||
      product.title.toLowerCase().includes(query) ||
      product.brand.toLowerCase().includes(query) ||
      product.subtitle.toLowerCase().includes(query);
    const matchesCategory = category === "all" || product.category === category;
    return product.status === "published" && matchesQuery && matchesCategory;
  });
  const categories = ["all", ...Array.from(new Set(demoProducts.map((item) => item.category)))];

  return (
    <UserCommerceShell active="products">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-5 md:px-6">
        <PageHeader
          eyebrow="商品浏览"
          title="精选商品"
          description="按类目、关键词和库存状态快速筛选，商品卡片保留价格、库存、品牌和详情入口。"
          action={
            <div className="flex flex-wrap gap-2">
              <Link className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-bold" href="/cart">
                购物车
              </Link>
              <Link className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-bold" href="/orders">
                我的订单
              </Link>
            </div>
          }
        />

        <form className="grid gap-3 rounded-md border border-slate-200 bg-white p-4 md:grid-cols-[1fr_220px_110px]">
          <label className="relative">
            <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-commerce-red" aria-hidden="true" />
            <input
              className="h-11 w-full rounded-md border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-commerce-red focus:ring-2 focus:ring-commerce-red/20"
              defaultValue={params.q}
              name="q"
              placeholder="搜索商品、品牌或关键词"
            />
          </label>
          <select
            className="h-11 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-commerce-red"
            defaultValue={category}
            name="category"
          >
            {categories.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "全部类目" : item}
              </option>
            ))}
          </select>
          <button className="flex h-11 items-center justify-center gap-2 rounded-md bg-commerce-ink px-4 text-sm font-bold text-white" type="submit">
            <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
            筛选
          </button>
        </form>

        <div className="flex flex-wrap gap-2">
          {["官方自营", "现货速发", "支持售后", "价保 7 天", "模拟支付"].map((item, index) => (
            <StatusPill tone={index === 0 ? "red" : index === 1 ? "teal" : "slate"} key={item}>
              {item}
            </StatusPill>
          ))}
        </div>

        {products.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="font-bold">没有匹配的上架商品</p>
            <p className="mt-2 text-sm text-slate-500">换个关键词，或查看全部类目。</p>
            <Link className="mt-5 inline-flex rounded-md bg-commerce-red px-4 py-2 text-sm font-bold text-white" href="/products">
              查看全部
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <ProductCard product={product} compact key={product.id} />
            ))}
          </div>
        )}
      </section>
    </UserCommerceShell>
  );
}
