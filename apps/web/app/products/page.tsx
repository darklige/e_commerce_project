import Link from "next/link";

import { availableStock, demoProducts, formatPrice } from "@/lib/catalog-demo";

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
      product.brand.toLowerCase().includes(query);
    const matchesCategory = category === "all" || product.category === category;
    return product.status === "published" && matchesQuery && matchesCategory;
  });
  const categories = ["all", ...Array.from(new Set(demoProducts.map((item) => item.category)))];

  return (
    <main className="min-h-screen bg-[#f6f7f9] px-4 py-6 text-commerce-ink md:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold text-commerce-red">商品浏览</p>
            <h1 className="mt-1 text-2xl font-semibold">精选商品</h1>
          </div>
          <Link className="text-sm font-semibold text-commerce-teal" href="/">
            返回工作台
          </Link>
        </header>

        <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[1fr_220px_96px]">
          <input
            className="h-11 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
            defaultValue={params.q}
            name="q"
            placeholder="搜索商品或品牌"
          />
          <select
            className="h-11 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-commerce-teal"
            defaultValue={category}
            name="category"
          >
            {categories.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "全部类目" : item}
              </option>
            ))}
          </select>
          <button className="h-11 rounded-md bg-commerce-ink px-4 text-sm font-semibold text-white" type="submit">
            筛选
          </button>
        </form>

        {products.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-600">
            没有匹配的上架商品。
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {products.map((product) => (
              <article className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm" key={product.id}>
                <div
                  aria-label={product.title}
                  className="aspect-[4/3] w-full bg-cover bg-center"
                  role="img"
                  style={{ backgroundImage: `url(${product.image})` }}
                />
                <div className="flex min-h-52 flex-col gap-3 p-4">
                  <div>
                    <p className="text-xs font-semibold text-slate-500">{product.brand}</p>
                    <h2 className="mt-1 text-lg font-semibold">{product.title}</h2>
                    <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">{product.subtitle}</p>
                  </div>
                  <div className="mt-auto flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-commerce-red">{formatPrice(product.price)}</p>
                      <p className="text-xs text-slate-500">可售库存 {availableStock(product)}</p>
                    </div>
                    <Link
                      className="rounded-md border border-commerce-teal px-3 py-2 text-sm font-semibold text-commerce-teal"
                      href={`/products/${product.id}`}
                    >
                      查看
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
