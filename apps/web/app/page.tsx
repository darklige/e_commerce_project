import Link from "next/link";
import { Gift, Headphones, Laptop, PackageCheck, Smartphone, Sparkles, TabletSmartphone, Truck } from "lucide-react";

import {
  ProductCard,
  PromoRibbon,
  ServiceStrip,
  UserCommerceShell,
  UserUtilityPanel
} from "@/components/user-commerce";
import { demoProducts } from "@/lib/catalog-demo";

const categoryLinks = [
  { label: "手机数码", icon: Smartphone, href: "/products?category=手机数码" },
  { label: "电脑办公", icon: Laptop, href: "/products?category=电脑办公" },
  { label: "智能配件", icon: Headphones, href: "/products?category=智能配件" },
  { label: "平板专区", icon: TabletSmartphone, href: "/products?q=pad" },
  { label: "极速配送", icon: Truck, href: "/orders" },
  { label: "售后保障", icon: PackageCheck, href: "/after-sales" }
];

export default function HomePage() {
  const publishedProducts = demoProducts.filter((product) => product.status === "published");

  return (
    <UserCommerceShell active="home">
      <section className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
        <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)_280px]">
          <aside className="rounded-md border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <p className="font-black">全部频道</p>
              <Sparkles className="h-4 w-4 text-commerce-red" aria-hidden="true" />
            </div>
            <nav className="mt-3 grid gap-1">
              {categoryLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    className="flex items-center justify-between rounded-md px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-red-50 hover:text-commerce-red"
                    href={item.href}
                    key={item.label}
                  >
                    <span className="flex items-center gap-2">
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      {item.label}
                    </span>
                    <span className="text-slate-300">›</span>
                  </Link>
                );
              })}
            </nav>
          </aside>

          <section className="overflow-hidden rounded-md bg-white">
            <div className="grid min-h-[360px] gap-0 md:grid-cols-[1fr_260px]">
              <div className="relative flex flex-col justify-between bg-[linear-gradient(135deg,#d71920_0%,#f97316_52%,#007d78_100%)] p-6 text-white md:p-8">
                <div>
                  <p className="text-sm font-bold uppercase tracking-[0.08em] text-white/80">M5 Hardening Launch</p>
                  <h1 className="mt-4 max-w-xl text-4xl font-black tracking-normal md:text-5xl">
                    像真实商城一样浏览、下单、追踪售后
                  </h1>
                  <p className="mt-4 max-w-xl text-base leading-7 text-white/85">
                    从精选商品到购物车、确认订单、模拟支付和客服介入，把用户主链路放在第一屏。
                  </p>
                </div>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Link className="rounded-md bg-white px-5 py-3 text-sm font-bold text-commerce-red" href="/products">
                    浏览商品
                  </Link>
                  <Link className="rounded-md border border-white/50 px-5 py-3 text-sm font-bold text-white" href="/after-sales">
                    查看售后
                  </Link>
                </div>
              </div>
              <div className="grid content-between gap-3 bg-[#fff7ed] p-5">
                <div>
                  <p className="text-sm font-bold text-commerce-red">今日精选</p>
                  <h2 className="mt-1 text-2xl font-black">Northstar X1</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">旗舰手机现货发售，库存锁定和售后状态全链路可演示。</p>
                </div>
                <div
                  aria-label="Northstar X1 手机"
                  className="aspect-[4/3] rounded-md bg-cover bg-center"
                  role="img"
                  style={{ backgroundImage: `url(${publishedProducts[0]?.image})` }}
                />
              </div>
            </div>
          </section>

          <UserUtilityPanel />
        </div>

        <ServiceStrip />
        <PromoRibbon />

        <section className="grid gap-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-bold text-commerce-red">猜你喜欢</p>
              <h2 className="mt-1 text-2xl font-black">精选商品</h2>
            </div>
            <Link className="text-sm font-bold text-commerce-red" href="/products">
              查看全部
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {publishedProducts.map((product) => (
              <ProductCard product={product} key={product.id} />
            ))}
          </div>
        </section>

        <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-4 md:grid-cols-3">
          {[
            { label: "订单状态", value: "支付成功后等待商家发货", icon: Gift },
            { label: "售后进度", value: "商家待处理，超时将升级客服", icon: PackageCheck },
            { label: "配送服务", value: "北京、上海核心区域支持极速达", icon: Truck }
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Link className="flex items-center gap-3 rounded-md bg-slate-50 p-4" href="/orders" key={item.label}>
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-white text-commerce-red">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span>
                  <span className="block text-sm font-bold">{item.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">{item.value}</span>
                </span>
              </Link>
            );
          })}
        </section>
      </section>
    </UserCommerceShell>
  );
}
