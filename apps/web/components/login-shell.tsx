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
    <main className="min-h-screen bg-[#f6f7f9] px-6 py-8 text-commerce-ink">
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-8 lg:grid-cols-[1fr_420px] lg:items-center">
        <div className="flex flex-col gap-5">
          <p className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500">
            {eyebrow}
          </p>
          <h1 className="max-w-2xl text-3xl font-semibold">{title}</h1>
          <p className="max-w-2xl text-base leading-7 text-slate-600">{description}</p>
        </div>

        <form className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className={`mb-5 h-1.5 w-16 rounded-full ${accentClassName}`} />
          <h2 className="text-xl font-semibold">{audience}登录</h2>
          <div className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              邮箱
              <input
                className="h-11 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                name="email"
                type="email"
                autoComplete="email"
              />
            </label>
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              密码
              <input
                className="h-11 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                name="password"
                type="password"
                autoComplete="current-password"
              />
            </label>
            <button
              className="mt-2 h-11 rounded-md bg-commerce-ink px-4 text-sm font-semibold text-white transition hover:bg-slate-700"
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
