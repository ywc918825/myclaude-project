# 梳妆台管家 — 原型

化妆品/护肤品保质期管理 + 成分冲突提示 + 消费报表的可运行 MVP 原型。

架构、数据模型、接口契约见 [DESIGN.md](./DESIGN.md)。

## 快速开始

```bash
# 终端1
cd backend/core-api && npm install && npm run dev

# 终端2
cd backend/reminder-api && npm install && npm run dev

# 终端3
cd frontend && npm install && npm run dev
```

浏览器打开 `https://localhost:5173`（注意是 https，自签名证书会有安全提示，点"继续访问"即可）。手机测试见 [DESIGN.md](./DESIGN.md#为什么前端dev-server是https以及手机怎么访问)。
