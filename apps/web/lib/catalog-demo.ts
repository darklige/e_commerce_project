export type DemoSku = {
  code: string;
  spec: string;
  price: number;
  stock: number;
  reserved: number;
};

export type DemoProduct = {
  id: string;
  title: string;
  subtitle: string;
  category: string;
  brand: string;
  status: "published" | "draft" | "unpublished";
  image: string;
  price: number;
  stockRisk: "充足" | "偏低" | "售罄";
  skus: DemoSku[];
};

export const demoProducts: DemoProduct[] = [
  {
    id: "northstar-x1",
    title: "Northstar X1",
    subtitle: "旗舰性能手机，曜石黑 / 星银双规格",
    category: "手机数码",
    brand: "Northstar",
    status: "published",
    image: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80",
    price: 399900,
    stockRisk: "充足",
    skus: [
      { code: "NS-X1-BLACK-256", spec: "曜石黑 / 256GB", price: 399900, stock: 8, reserved: 4 },
      { code: "NS-X1-SILVER-512", spec: "星银 / 512GB", price: 459900, stock: 2, reserved: 0 }
    ]
  },
  {
    id: "aurora-pad-11",
    title: "Aurora Pad 11",
    subtitle: "轻薄平板，适合移动办公与影音娱乐",
    category: "电脑办公",
    brand: "Aurora",
    status: "draft",
    image: "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80",
    price: 289900,
    stockRisk: "偏低",
    skus: [
      { code: "AP11-GRAY-128", spec: "深空灰 / 128GB", price: 289900, stock: 3, reserved: 1 },
      { code: "AP11-BLUE-256", spec: "海雾蓝 / 256GB", price: 329900, stock: 1, reserved: 0 }
    ]
  },
  {
    id: "terra-headset-pro",
    title: "Terra Headset Pro",
    subtitle: "主动降噪耳机，长续航充电盒",
    category: "智能配件",
    brand: "Terra",
    status: "published",
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
    price: 89900,
    stockRisk: "售罄",
    skus: [
      { code: "THP-WHITE", spec: "云白", price: 89900, stock: 0, reserved: 0 },
      { code: "THP-BLACK", spec: "曜黑", price: 89900, stock: 0, reserved: 0 }
    ]
  }
];

export function formatPrice(cents: number) {
  return `¥${(cents / 100).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

export function availableStock(product: DemoProduct) {
  return product.skus.reduce((total, sku) => total + Math.max(0, sku.stock - sku.reserved), 0);
}
