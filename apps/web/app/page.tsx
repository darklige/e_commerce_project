import Link from "next/link";

const surfaces = [
  { name: "用户网页端", status: "M4 after-sales tracking", accent: "bg-commerce-red" },
  { name: "商家后台", status: "M4 service queue", accent: "bg-commerce-teal" },
  { name: "管理员后台", status: "M4 work orders", accent: "bg-commerce-gold" }
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-6 py-8 text-commerce-ink">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.08em] text-commerce-red">
            M4 After-Sales Workflow
          </p>
          <h1 className="text-3xl font-semibold">Commerce Platform</h1>
          <p className="max-w-3xl text-base leading-7 text-slate-600">
            当前阶段已扩展售后退款、商家审核、客服介入和工单处理，
            并让用户端、商家后台、管理员后台围绕同一售后状态机协同。
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
          <Link className="rounded-md bg-white px-4 py-3 text-sm font-semibold text-commerce-red" href="/after-sales">
            我的售后
          </Link>
          <Link className="rounded-md bg-commerce-teal px-4 py-3 text-sm font-semibold text-white" href="/merchant/products">
            商家商品管理
          </Link>
          <Link className="rounded-md bg-white px-4 py-3 text-sm font-semibold text-commerce-teal" href="/merchant/after-sales">
            商家售后
          </Link>
          <Link className="rounded-md bg-white px-4 py-3 text-sm font-semibold text-commerce-ink" href="/admin/work-orders">
            客服工单
          </Link>
        </div>
      </section>
    </main>
  );
}
