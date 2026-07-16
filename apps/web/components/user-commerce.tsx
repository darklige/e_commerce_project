import Link from "next/link";
import type { ComponentType, ReactNode } from "react";
import {
  BadgeCheck,
  Bell,
  ChevronRight,
  Clock3,
  MapPin,
  PackageCheck,
  Search,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Truck,
  UserRound,
  WalletCards
} from "lucide-react";

import { availableStock, type DemoProduct, formatPrice } from "@/lib/catalog-demo";

type UserShellProps = {
  children: ReactNode;
  active?: "home" | "products" | "cart" | "orders" | "after-sales";
};

const navItems = [
  { href: "/", label: "首页", key: "home" },
  { href: "/products", label: "精选商品", key: "products" },
  { href: "/cart", label: "购物车", key: "cart" },
  { href: "/orders", label: "我的订单", key: "orders" },
  { href: "/after-sales", label: "售后进度", key: "after-sales" }
];

export function UserCommerceShell({ children, active }: UserShellProps) {
  return (
    <main className="min-h-screen bg-[#f4f5f7] text-commerce-ink">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:px-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <Link className="flex items-center gap-2" href="/">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-commerce-red text-sm font-black text-white">
                C
              </span>
              <span>
                <span className="block text-base font-black leading-5">Commerce</span>
                <span className="block text-xs font-semibold text-slate-500">M5 Hardening Launch</span>
              </span>
            </Link>

            <form className="flex min-w-0 flex-1 items-center md:max-w-2xl" action="/products">
              <label className="relative flex min-w-0 flex-1 items-center">
                <Search className="pointer-events-none absolute left-3 h-4 w-4 text-commerce-red" aria-hidden="true" />
                <input
                  className="h-11 w-full rounded-l-md border border-commerce-red bg-white pl-10 pr-3 text-sm outline-none transition focus:ring-2 focus:ring-commerce-red/20"
                  name="q"
                  placeholder="手机、耳机、平板、办公好物"
                />
              </label>
              <button className="flex h-11 items-center gap-2 rounded-r-md bg-commerce-red px-5 text-sm font-semibold text-white" type="submit">
                <Search className="h-4 w-4" aria-hidden="true" />
                搜索
              </button>
            </form>

            <div className="flex items-center gap-2 text-sm">
              <Link className="flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 font-semibold text-slate-700" href="/login">
                <UserRound className="h-4 w-4 text-commerce-red" aria-hidden="true" />
                登录
              </Link>
              <Link className="flex h-10 items-center gap-2 rounded-md bg-commerce-ink px-3 font-semibold text-white" href="/cart">
                <ShoppingCart className="h-4 w-4" aria-hidden="true" />
                购物车
              </Link>
            </div>
          </div>

          <nav className="flex gap-2 overflow-x-auto text-sm font-semibold text-slate-600">
            {navItems.map((item) => (
              <Link
                className={
                  active === item.key
                    ? "whitespace-nowrap rounded-md bg-commerce-red px-3 py-2 text-white"
                    : "whitespace-nowrap rounded-md px-3 py-2 transition hover:bg-slate-100 hover:text-commerce-red"
                }
                href={item.href}
                key={item.key}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      {children}
    </main>
  );
}

export function ServiceStrip() {
  const services = [
    { icon: ShieldCheck, label: "正品保障" },
    { icon: Truck, label: "极速达" },
    { icon: BadgeCheck, label: "价保服务" },
    { icon: PackageCheck, label: "售后无忧" }
  ];
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {services.map((service) => {
        const Icon = service.icon;
        return (
          <div className="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-3" key={service.label}>
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-red-50 text-commerce-red">
              <Icon className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="text-sm font-semibold">{service.label}</span>
          </div>
        );
      })}
    </div>
  );
}

type ProductCardProps = {
  product: DemoProduct;
  compact?: boolean;
};

export function ProductCard({ product, compact = false }: ProductCardProps) {
  const stock = availableStock(product);
  const soldOut = stock === 0;
  return (
    <article className="group overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-commerce-red/40 hover:shadow-md">
      <Link className="block" href={`/products/${product.id}`}>
        <div
          aria-label={product.title}
          className={compact ? "aspect-[5/4] w-full bg-cover bg-center" : "aspect-square w-full bg-cover bg-center"}
          role="img"
          style={{ backgroundImage: `url(${product.image})` }}
        />
      </Link>
      <div className="flex min-h-48 flex-col gap-3 p-4">
        <div>
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold text-slate-500">{product.brand}</p>
            <span className={soldOut ? "rounded px-2 py-1 text-xs font-semibold text-commerce-red" : "rounded px-2 py-1 text-xs font-semibold text-commerce-teal"}>
              {stock > 0 ? `现货 ${stock}` : "暂时无货"}
            </span>
          </div>
          <h2 className="mt-2 line-clamp-1 text-base font-bold">{product.title}</h2>
          <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">{product.subtitle}</p>
        </div>
        <div className="mt-auto flex items-end justify-between gap-3">
          <div>
            <p className="text-xl font-black text-commerce-red">{formatPrice(product.price)}</p>
            <p className="mt-1 text-xs text-slate-500">{product.category}</p>
          </div>
          <Link
            className="flex h-10 items-center gap-1 rounded-md bg-commerce-red px-3 text-sm font-semibold text-white"
            href={`/products/${product.id}`}
          >
            选购
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </article>
  );
}

type StatusPillProps = {
  children: ReactNode;
  tone?: "red" | "teal" | "gold" | "slate";
};

export function StatusPill({ children, tone = "slate" }: StatusPillProps) {
  const tones = {
    red: "bg-red-50 text-commerce-red ring-red-100",
    teal: "bg-emerald-50 text-commerce-teal ring-emerald-100",
    gold: "bg-amber-50 text-amber-700 ring-amber-100",
    slate: "bg-slate-100 text-slate-700 ring-slate-200"
  };
  return (
    <span className={`inline-flex w-fit items-center rounded-md px-2.5 py-1 text-xs font-bold ring-1 ${tones[tone]}`}>
      {children}
    </span>
  );
}

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-sm font-bold text-commerce-red">{eyebrow}</p>
        <h1 className="mt-1 text-2xl font-black tracking-normal md:text-3xl">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">{description}</p>
      </div>
      {action}
    </header>
  );
}

type TimelineStep = {
  label: string;
  time: string;
  tone?: string;
};

export function Timeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <div className="grid gap-3">
      {steps.map((step, index) => (
        <div className="grid grid-cols-[28px_1fr] gap-3" key={`${step.label}-${step.time}`}>
          <div className="flex flex-col items-center">
            <span className={step.tone === "current" ? "h-7 w-7 rounded-full bg-commerce-red text-center text-sm font-bold leading-7 text-white" : "h-7 w-7 rounded-full bg-emerald-100 text-center text-sm font-bold leading-7 text-commerce-teal"}>
              {index + 1}
            </span>
            {index < steps.length - 1 ? <span className="mt-2 h-9 w-px bg-slate-200" /> : null}
          </div>
          <div className="pb-3">
            <p className={step.tone === "current" ? "font-bold text-commerce-red" : "font-semibold"}>{step.label}</p>
            <p className="mt-1 text-xs text-slate-500">{step.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function UserUtilityPanel() {
  return (
    <aside className="grid gap-3">
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-md bg-commerce-ink text-white">
            <UserRound className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="font-bold">晚上好，欢迎回来</p>
            <p className="mt-1 text-xs text-slate-500">登录后同步购物车、订单和售后进度</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Link className="rounded-md bg-commerce-red px-3 py-2 text-center text-sm font-semibold text-white" href="/login">
            立即登录
          </Link>
          <Link className="rounded-md border border-slate-200 px-3 py-2 text-center text-sm font-semibold" href="/orders">
            查订单
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { icon: WalletCards, label: "优惠券", value: "3 张" },
          { icon: Bell, label: "待提醒", value: "2 条" },
          { icon: Clock3, label: "售后时限", value: "18h" },
          { icon: MapPin, label: "配送城市", value: "北京" }
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Link className="rounded-md border border-slate-200 bg-white p-3" href="/orders" key={item.label}>
              <Icon className="h-4 w-4 text-commerce-red" aria-hidden="true" />
              <p className="mt-2 text-xs text-slate-500">{item.label}</p>
              <p className="mt-1 text-sm font-bold">{item.value}</p>
            </Link>
          );
        })}
      </div>
    </aside>
  );
}

export function PromoRibbon() {
  return (
    <div className="flex flex-col gap-3 rounded-md bg-[linear-gradient(135deg,#d71920_0%,#f97316_55%,#007d78_100%)] p-4 text-white md:flex-row md:items-center md:justify-between">
      <div>
        <p className="flex items-center gap-2 text-sm font-bold">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          新品补贴日
        </p>
        <p className="mt-1 text-xl font-black">手机数码低至 8 折，售后极速响应</p>
      </div>
      <Link className="w-fit rounded-md bg-white px-4 py-2 text-sm font-bold text-commerce-red" href="/products">
        去抢购
      </Link>
    </div>
  );
}

export function QuickIconLink({
  href,
  label,
  icon: Icon
}: {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
}) {
  return (
    <Link className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-commerce-red hover:text-commerce-red" href={href}>
      <Icon className="h-4 w-4" aria-hidden={true} />
      {label}
    </Link>
  );
}
