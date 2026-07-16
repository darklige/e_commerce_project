import Link from "next/link";
import { LockKeyhole, Mail, ShieldCheck, ShoppingBag, Smartphone, UserRound } from "lucide-react";

export default function UserLoginPage() {
  return (
    <main className="min-h-screen bg-[#f4f5f7] text-commerce-ink">
      <section className="mx-auto grid min-h-screen max-w-7xl gap-6 px-4 py-6 md:px-6 lg:grid-cols-[minmax(0,1fr)_420px] lg:items-center">
        <div className="relative overflow-hidden rounded-md bg-[linear-gradient(135deg,#d71920_0%,#f97316_55%,#007d78_100%)] p-6 text-white md:p-10">
          <Link className="inline-flex items-center gap-2 rounded-md bg-white/15 px-3 py-2 text-sm font-bold" href="/">
            <ShoppingBag className="h-4 w-4" aria-hidden="true" />
            Commerce
          </Link>
          <div className="mt-14 max-w-2xl">
            <p className="text-sm font-bold uppercase tracking-[0.08em] text-white/80">User Shopping Login</p>
            <h1 className="mt-3 text-4xl font-black tracking-normal md:text-5xl">登录后继续你的购物、订单和售后进度</h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/85">
              保留购物车选择，查看支付倒计时，随时跟踪商家审核和客服介入状态。
            </p>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-3">
            {[
              { icon: Smartphone, label: "多端同步" },
              { icon: ShieldCheck, label: "账号保护" },
              { icon: ShoppingBag, label: "交易跟踪" }
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div className="rounded-md bg-white/10 p-4 backdrop-blur" key={item.label}>
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <p className="mt-3 text-sm font-bold">{item.label}</p>
                </div>
              );
            })}
          </div>
        </div>

        <form className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-red-50 text-commerce-red">
              <UserRound className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-2xl font-black">用户登录</h2>
              <p className="mt-1 text-sm text-slate-500">演示账号可直接填写任意邮箱与密码</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <label className="grid gap-2 text-sm font-semibold text-slate-700">
              邮箱或手机号
              <span className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-red focus:ring-2 focus:ring-commerce-red/20"
                  autoComplete="email"
                  name="email"
                  placeholder="user@example.com"
                  type="email"
                />
              </span>
            </label>
            <label className="grid gap-2 text-sm font-semibold text-slate-700">
              密码
              <span className="relative">
                <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-red focus:ring-2 focus:ring-commerce-red/20"
                  autoComplete="current-password"
                  name="password"
                  placeholder="请输入密码"
                  type="password"
                />
              </span>
            </label>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-slate-600">
                <input className="h-4 w-4 accent-commerce-red" type="checkbox" />
                7 天内免登录
              </label>
              <Link className="font-semibold text-commerce-red" href="/login">
                找回账号
              </Link>
            </div>

            <button className="flex h-12 items-center justify-center gap-2 rounded-md bg-commerce-red px-4 text-sm font-bold text-white" type="button">
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              登录并继续购物
            </button>
          </div>

          <div className="mt-6 border-t border-slate-100 pt-5">
            <p className="text-sm font-semibold">快速进入</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <Link className="rounded-md border border-slate-200 px-3 py-2 text-center text-sm font-semibold" href="/cart">
                购物车
              </Link>
              <Link className="rounded-md border border-slate-200 px-3 py-2 text-center text-sm font-semibold" href="/orders">
                我的订单
              </Link>
            </div>
          </div>
        </form>
      </section>
    </main>
  );
}
