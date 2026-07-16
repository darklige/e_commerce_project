import { demoProducts } from "@/lib/catalog-demo";

const x1 = demoProducts.find((item) => item.id === "northstar-x1");
const headset = demoProducts.find((item) => item.id === "terra-headset-pro");

export const demoCartItems = [
  {
    id: "cart-northstar-x1",
    product: x1!,
    sku: x1!.skus[0],
    quantity: 1,
    selected: true
  },
  {
    id: "cart-terra-headset",
    product: headset!,
    sku: headset!.skus[0],
    quantity: 1,
    selected: false
  }
];

export const demoOrders = [
  {
    id: "order-20260716001",
    orderNo: "JD202607160001",
    status: "paid_pending_shipment",
    statusText: "已支付待发货",
    createdAt: "2026-07-16 17:20",
    expiresAt: "2026-07-16 17:50",
    receiver: "张三",
    phone: "13800000000",
    address: "北京市朝阳区测试路 1 号",
    items: [
      {
        product: x1!,
        sku: x1!.skus[0],
        quantity: 1,
        paidPrice: x1!.skus[0].price
      }
    ],
    timeline: [
      { label: "提交订单", time: "17:20", tone: "done" },
      { label: "库存锁定", time: "17:20", tone: "done" },
      { label: "模拟支付成功", time: "17:22", tone: "done" },
      { label: "等待商家发货", time: "处理中", tone: "current" }
    ]
  },
  {
    id: "order-20260716002",
    orderNo: "JD202607160002",
    status: "pending_payment",
    statusText: "待支付",
    createdAt: "2026-07-16 17:42",
    expiresAt: "2026-07-16 18:12",
    receiver: "李四",
    phone: "13900000000",
    address: "上海市浦东新区演示街 88 号",
    items: [
      {
        product: x1!,
        sku: x1!.skus[1],
        quantity: 1,
        paidPrice: x1!.skus[1].price
      }
    ],
    timeline: [
      { label: "提交订单", time: "17:42", tone: "done" },
      { label: "库存锁定", time: "17:42", tone: "done" },
      { label: "待模拟支付", time: "剩余 30 分钟", tone: "current" }
    ]
  }
];

export function cartLineTotal(item: (typeof demoCartItems)[number]) {
  return item.sku.price * item.quantity;
}

export function orderTotal(order: (typeof demoOrders)[number]) {
  return order.items.reduce((total, item) => total + item.paidPrice * item.quantity, 0);
}

export function selectedCartTotal() {
  return demoCartItems
    .filter((item) => item.selected)
    .reduce((total, item) => total + cartLineTotal(item), 0);
}

export function selectedCartCount() {
  return demoCartItems
    .filter((item) => item.selected)
    .reduce((total, item) => total + item.quantity, 0);
}
