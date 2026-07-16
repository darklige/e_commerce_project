type LoginShellProps = {
  audience: "管理员" | "商家";
  eyebrow: string;
  title: string;
  description: string;
  accentClassName: string;
};

export function LoginShell({
  audience,
  eyebrow,
  title,
  description,
  accentClassName
}: LoginShellProps) {
  return (
    <main className="min-h-screen bg-[#f4f5f7] px-4 py-6 text-commerce-ink md:px-6">
      <section className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-7xl gap-6 lg:grid-cols-[1fr_420px] lg:items-center">
        <div className="rounded-md bg-white p-6 md:p-10">
          <p className="text-sm font-bold uppercase tracking-[0.08em] text-slate-500">
            {eyebrow}
          </p>
          <h1 className="mt-4 max-w-2xl text-4xl font-black tracking-normal">{title}</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">{description}</p>
          <div className="mt-8 grid gap-3 md:grid-cols-3">
            {["权限隔离", "审计留痕", "状态联动"].map((item) => (
              <div className="rounded-md bg-slate-50 p-4" key={item}>
                <p className="text-sm font-bold">{item}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">按角色进入对应工作台</p>
              </div>
            ))}
          </div>
        </div>

        <form className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <div className={`mb-5 h-1.5 w-16 rounded-full ${accentClassName}`} />
          <h2 className="text-2xl font-black">{audience}登录</h2>
          <p className="mt-2 text-sm text-slate-500">演示环境暂不提交真实凭证。</p>
          <div className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-2 text-sm font-bold text-slate-700">
              邮箱
              <input
                className="h-12 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                name="email"
                type="email"
                autoComplete="email"
              />
            </label>
            <label className="flex flex-col gap-2 text-sm font-bold text-slate-700">
              密码
              <input
                className="h-12 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                name="password"
                type="password"
                autoComplete="current-password"
              />
            </label>
            <button
              className="mt-2 h-12 rounded-md bg-commerce-ink px-4 text-sm font-bold text-white transition hover:bg-slate-700"
              type="button"
            >
              登录
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
