import { demoOrders } from "@/lib/order-demo";

const paidOrder = demoOrders[0];
const pendingOrder = demoOrders[1];

export const demoAfterSales = [
  {
    id: "as-20260716001",
    no: "AS202607160001",
    orderNo: paidOrder.orderNo,
    status: "merchant_review",
    statusText: "商家待处理",
    typeText: "退货退款",
    risk: "高",
    deadline: "剩余 18 小时",
    merchant: "Northstar 自营旗舰店",
    refundAmount: 399900,
    reason: "商品存在质量问题",
    customerNote: "开机后屏幕闪烁，已上传检测照片。",
    nextAction: "商家需审核，超时将升级平台客服",
    item: paidOrder.items[0],
    timeline: [
      { time: "17:50", label: "用户提交退货退款申请" },
      { time: "17:51", label: "系统通知商家处理" }
    ]
  },
  {
    id: "as-20260716002",
    no: "AS202607160002",
    orderNo: pendingOrder.orderNo,
    status: "waiting_buyer_return",
    statusText: "待买家退货",
    typeText: "退货退款",
    risk: "中",
    deadline: "剩余 6 天",
    merchant: "Northstar 自营旗舰店",
    refundAmount: 459900,
    reason: "七天无理由退货",
    customerNote: "包装完整，等待填写物流单号。",
    nextAction: "用户填写退货物流",
    item: pendingOrder.items[0],
    timeline: [
      { time: "17:42", label: "用户提交申请" },
      { time: "17:45", label: "商家同意退货退款" }
    ]
  },
  {
    id: "as-20260716003",
    no: "AS202607160003",
    orderNo: paidOrder.orderNo,
    status: "refund_failed",
    statusText: "退款失败",
    typeText: "仅退款",
    risk: "高",
    deadline: "人工处理",
    merchant: "Northstar 自营旗舰店",
    refundAmount: 89900,
    reason: "少发配件",
    customerNote: "商家已同意，仅退款失败，等待平台财务重试。",
    nextAction: "平台财务重试模拟退款",
    item: paidOrder.items[0],
    timeline: [
      { time: "16:02", label: "商家同意仅退款" },
      { time: "16:03", label: "模拟退款失败：channel timeout" },
      { time: "16:05", label: "生成客服工单" }
    ]
  },
  {
    id: "as-20260716004",
    no: "AS202607160004",
    orderNo: paidOrder.orderNo,
    status: "refunded",
    statusText: "退款成功",
    typeText: "退货退款",
    risk: "低",
    deadline: "已完成",
    merchant: "Northstar 自营旗舰店",
    refundAmount: 399900,
    reason: "仓库确认收货",
    customerNote: "退款已按原路退回。",
    nextAction: "售后完成",
    item: paidOrder.items[0],
    timeline: [
      { time: "15:20", label: "用户寄回商品" },
      { time: "15:52", label: "商家确认收货" },
      { time: "15:53", label: "模拟退款成功" }
    ]
  }
];

export const demoWorkOrders = [
  {
    id: "wo-20260716001",
    no: "WO202607160001",
    afterSales: demoAfterSales[2],
    queue: "退款异常",
    assignee: "平台财务",
    priority: "高",
    status: "open",
    statusText: "待处理",
    reason: "模拟退款失败，需要财务重试或人工确认",
    evidenceSummary: "用户诉求：少发配件；凭证数量：2；商家说明：同意仅退款；退款失败：channel timeout",
    internalNotes: "财务需核对模拟退款流水，重试前确认没有重复退款单。"
  },
  {
    id: "wo-20260716002",
    no: "WO202607160002",
    afterSales: demoAfterSales[0],
    queue: "商家超时风险",
    assignee: "平台客服",
    priority: "高",
    status: "open",
    statusText: "待商家响应",
    reason: "商家审核剩余时间不足，需跟进",
    evidenceSummary: "用户诉求：商品存在质量问题；凭证数量：1；用户说明：开机后屏幕闪烁",
    internalNotes: "客服先联系商家，超时后升级主管裁决。"
  }
];
