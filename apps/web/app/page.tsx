const surfaces = [
  { name: "用户网页端", status: "M0 shell", accent: "bg-commerce-red" },
  { name: "商家后台", status: "M0 shell", accent: "bg-commerce-teal" },
  { name: "管理员后台", status: "M0 shell", accent: "bg-commerce-gold" }
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] px-6 py-8 text-commerce-ink">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.08em] text-commerce-red">
            M0 Foundation
          </p>
          <h1 className="text-3xl font-semibold">Commerce Platform</h1>
          <p className="max-w-3xl text-base leading-7 text-slate-600">
            多端电商平台基础工程已启动。当前页面用于验证 Next.js、Tailwind CSS
            和多端入口规划，后续会逐步拆分用户端、商家后台、管理员后台工作台。
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
      </section>
    </main>
  );
}

