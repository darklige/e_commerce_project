import Link from "next/link";

const surfaces = [
  { name: "用户网页端", status: "M3 shopping workflow", accent: "bg-commerce-red" },
  { name: "商家后台", status: "M3 order visibility", accent: "bg-commerce-teal" },
  { name: "管理员后台", status: "M3 order governance", accent: "bg-commerce-gold" }
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-6 py-8 text-commerce-ink">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.08em] text-commerce-red">
            M3 Order Workflow
          </p>
          <h1 className="text-3xl font-semibold">Commerce Platform</h1>
          <p className="max-w-3xl text-base leading-7 text-slate-600">
            当前阶段已串起商品浏览、购物车、结算、订单创建、库存锁定和模拟支付，
            后端以订单状态机、幂等键、库存预留和审计日志保证核心交易链路一致。
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-3">
          {surfaces.map((surface) => (
            <article
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              key={surface.name}
            >
              <div className={`mb-4 h-1.5 w-16 rounded-full ${surface.accent}`} />
              <h2 className="text-lg font-semibold">{surface.name}</h2>
              <p className="mt-2 text-sm text-slate-600">{surface.status}</p>
            </article>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <Link className="rounded-md bg-commerce-red px-4 py-3 text-sm font-semibold text-white" href="/products">
            浏览商品
          </Link>
          <Link className="rounded-md bg-commerce-ink px-4 py-3 text-sm font-semibold text-white" href="/cart">
            购物车
          </Link>
          <Link className="rounded-md bg-commerce-gold px-4 py-3 text-sm font-semibold text-commerce-ink" href="/orders">
            我的订单
          </Link>
          <Link className="rounded-md bg-commerce-teal px-4 py-3 text-sm font-semibold text-white" href="/merchant/products">
            商家商品管理
          </Link>
        </div>
      </section>
    </main>
  );
}
