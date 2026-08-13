# 梳妆台管家 — 可运行原型 · 架构与接口契约

一人公司MVP原型，验证"化妆品保质期管理 + 成分冲突提示 + 消费报表"这个产品方向。
四个工作流并行开发，彼此以本文档的接口契约为准，禁止修改契约本身（如需变更需在本文件里改并同步通知）。

## 目录结构

```
backend/core-api/       # 后端A：产品与柜子 CRUD（端口 4001）
backend/reminder-api/   # 后端B：成分冲突检测 + 消费报表（端口 4002）
frontend/               # 前端 Vite + React 单页应用（端口 5173）
  src/pages/cabinet/     # 前端A：添加产品 + 柜子总览
  src/pages/report/      # 前端B：提醒中心 + 消费报表
```

两个后端是完全独立的Node进程/独立数据源，互不调用（避免服务间耦合）。前端负责在需要时把 core-api 的产品数据传给 reminder-api 做二次计算（冲突检测、报表聚合）。

## 数据模型：Product（core-api 所有权）

```
{
  id: number,
  name: string,
  brand: string,
  category: "护肤" | "彩妆" | "身体护理",
  openedDate: string,       // "YYYY-MM-DD" 开封日期
  paoMonths: number,        // 开封后有效期（月），常见 6/12/18/24
  ingredientTags: string[], // 成分标签，从下方推荐词表中选
  costCNY: number,
  photoUrl: string | null,  // core-api 静态文件相对路径，如 "/uploads/xxx.jpg"，前端用 resolveUploadUrl() 拼成绝对地址
  createdAt: string,        // ISO datetime

  // 以下三个字段由 core-api 在返回时计算好，前端不需要自己算：
  expiryDate: string,       // openedDate + paoMonths，"YYYY-MM-DD"
  daysRemaining: number,    // 距离 expiryDate 的天数，可为负数（已过期）
  status: "ok" | "warning" | "expired"  // daysRemaining < 0 → expired；0-14 → warning；否则 ok
}
```

**推荐成分标签词表**（两个后端都用这套词，保证能匹配上）：
`维生素C`、`烟酰胺`、`视黄醇(A醇)`、`水杨酸`、`果酸(AHA)`、`苯氧乙醇`、`尿素`、`神经酰胺`、`玻尿酸`、`积雪草`、`熊果苷`、`传明酸`、`二裂酵母`、`维生素E`、`甘草酸二钾`

## core-api 接口（backend/core-api，端口 4001）

- `GET /api/categories` → `string[]`（已实现，不需要改）
- `GET /api/products` → `Product[]`
- `POST /api/products` body 为 Product 去掉 `id/createdAt/expiryDate/daysRemaining/status` → 返回创建后的完整 `Product`
- `GET /api/products/:id` → `Product`（不存在返回 404 `{error}`）
- `PUT /api/products/:id` body 同 POST → 返回更新后的完整 `Product`
- `DELETE /api/products/:id` → 204 无内容
- `POST /api/upload` body `{ imageBase64: "data:image/jpeg;base64,..." }` → `{ url: "/uploads/xxx.jpg" }`，图片落盘到 `backend/core-api/uploads/`（已 gitignore），并通过 `/uploads/*` 静态路由对外提供访问

`ingredientTags` 在数据库里以 JSON 字符串存储，API 出入参统一用数组，路由层负责转换。

## reminder-api 接口（backend/reminder-api，端口 4002）

- `GET /api/ingredient-rules` → `{a: string, b: string, reason: string}[]`（冲突规则表，至少覆盖4条，参考推荐词表里的组合，例如 维生素C+烟酰胺、视黄醇(A醇)+水杨酸、视黄醇(A醇)+果酸(AHA)、维生素C+视黄醇(A醇)）
- `POST /api/conflict-check` body `{ products: {id, name, ingredientTags}[] }` → 返回数组，每一项是两件产品之间命中的冲突：
  ```
  [{ productAId, productAName, productBId, productBName, ingredientA, ingredientB, reason }]
  ```
  逻辑：两两比较传入产品的 ingredientTags，命中规则表（任意方向）就记一条。
- `POST /api/report` body `{ products: Product[] }`（前端直接把 core-api 返回的完整产品数组转发过来）→ 返回：
  ```
  {
    totalItems: number,
    totalValueCNY: number,
    wastedValueCNY: number,        // status === "expired" 的 costCNY 之和
    categoryBreakdown: { [category: string]: number },
    monthlyOpened: { month: string, count: number, costCNY: number }[]  // 按 openedDate 的年月分组（"YYYY-MM"），按月份升序
  }
  ```

## 前端

- 单页应用，底部4个 tab：柜子 / 添加 / 提醒 / 报表，已在 `src/App.jsx` 搭好导航壳，四个页面组件各自独立文件，不要改 `App.jsx` 的路由逻辑本身（如确有必要要改，先在这里说明原因）。
- `src/api/coreApi.js`、`src/api/reminderApi.js` 已封装好 fetch 调用，直接 import 使用即可，不要重复造轮子。
- 视觉基调：粉白色系、圆角卡片、可爱治愈风，`src/styles.css` 已提供基础 class（`.card` `.field` `.btn-primary` `.progress-track/.progress-fill` `.badge` `.status-ok/.status-warning/.status-expired` 等），优先复用，不够再扩展。
- `status` 对应色值建议：ok=`var(--ok)`，warning=`var(--warning)`，expired=`var(--expired)`。

## 如何运行（四个进程，四个终端）

```
cd backend/core-api && npm install && npm run dev       # http://localhost:4001
cd backend/reminder-api && npm install && npm run dev   # http://localhost:4002
cd frontend && npm install && npm run dev                # http://localhost:5173
```

前端的 `coreApi.js`/`reminderApi.js` 用 `window.location.hostname` 而不是硬编码 `localhost` 拼接后端地址，所以用手机连同一WiFi访问电脑的局域网IP（如 `http://192.168.x.x:5173`）也能正常调用后端——这对测试"拍照识别"这种依赖真机摄像头的功能很重要。`vite.config.js` 已经设置 `host: true`，后端 `express` 默认监听 `0.0.0.0`，都不需要改。

## 单元测试

```
cd backend/core-api && npm test       # node --test，覆盖日期计算、输入校验
cd backend/reminder-api && npm test   # node --test，覆盖成分冲突匹配、报表聚合
cd frontend && npm test               # vitest run，覆盖各页面的纯函数逻辑
```

## 编辑产品 / 到期提醒通知

- 柜子列表每张卡片新增"编辑"按钮，复用 `AddProduct.jsx` 表单（`editingProduct` prop 存在即为编辑模式），保存走 `PUT /api/products/:id`；"删除"现在会弹确认框，避免误删。
- "提醒"页新增到期提醒通知开关：基于浏览器 `Notification` API，每天最多提醒一次（用 `localStorage` 去重），**仅在这个页面被打开时生效**——这不是真正的后台推送，需要后台推送得接入 service worker + 推送服务器，超出原型范围，如果要做留作后续路线图。

## 数据库：Node 内置 `node:sqlite`，不用 `better-sqlite3`

`backend/core-api/db.js` 用的是 Node 自带的 `node:sqlite`（`DatabaseSync`），不是 `better-sqlite3`。原因：`better-sqlite3` 是原生编译模块，装的时候如果没有对应Node版本的预编译二进制包，就会本地用 node-gyp 现场编译，需要装 Visual Studio Build Tools（Windows）或 Xcode Command Line Tools（Mac）——普通用户的电脑上大概率没装，`npm install` 会直接报错卡住。换成 `node:sqlite` 后完全不需要编译任何东西，装完 Node（>=22.5.0，本项目建议用较新的LTS）就能直接跑。

API 用法和 `better-sqlite3` 几乎一致（`db.prepare(sql).get/all/run(params)`、支持 `@name` 具名参数），唯一差别是没有 `.transaction()` 辅助方法，种子数据插入改成手写 `BEGIN`/`COMMIT`。控制台会打一行 `ExperimentalWarning: SQLite is an experimental feature`，这是Node自己的提示，不影响使用，忽略即可。

## 拍照识别（stage2）

- 纯客户端 OCR，用 `tesseract.js`（chi_sim+eng），不依赖任何云端OCR API/密钥，识别在浏览器本地完成。
- worker/wasm核心/语言包不走CDN，而是 `frontend/scripts/copy-tesseract-assets.cjs` 在 `npm install` 后（`postinstall`）自动从 `node_modules` 拷贝到 `public/tesseract-assets/`（已 gitignore，体积约50MB，不进git，每次 `npm install` 自动生成）。
- 识别只是"猜"产品名称（取识别文本里最长的一行做候选，自动预填 `name` 字段），用户仍需自行核对/修改——这是辅助录入，不是权威数据源。
- 照片本身通过 `coreApi.uploadImage()` 传给 `POST /api/upload` 落盘，返回的 `url` 存进 `photoUrl`；OCR识别和照片上传是两个独立异步流程，互不阻塞。

## 联网查询产品信息（stage2.5）

- 数据源：[Open Beauty Facts](https://world.openbeautyfacts.org)，开源众包化妆品数据库，免费、无需API Key，`frontend/src/api/openBeautyFacts.js` 直接从浏览器调用其公开搜索接口（`GET /api/v2/search`）。
- 在添加产品页，填了产品名称或品牌后可点"联网查询产品信息"，按 `品牌+名称` 搜索，展示最多5条候选结果，用户手动点选正确的一条（文本搜索匹配不够精确，不做自动选择/自动填入）。
- 选中后：品牌字段留空时会带入查到的品牌；成分方面用一份简单的中文成分词表↔英文INCI名对照表（`INCI_MATCH`，见 `openBeautyFacts.js`）在返回的 `ingredients_text`/`ingredients_text_zh` 里做子串匹配，命中的会自动勾选对应成分标签（只做增量勾选，不会取消用户已勾的）。这是粗略匹配，不是精确解析，UI上会注明数据来源并附完整成分表原文供用户自行核对。
- 已知局限：Open Beauty Facts 以欧美品牌数据为主，国产/小众品牌命中率较低；这是文字搜索而非条码精确查询，后续如果要提升准确率可以加条码扫描（`GET /api/v2/product/{条码}.json`）。
- 沙盒环境说明：本项目的开发沙盒因出网策略屏蔽了对任意外部域名的访问，无法在沙盒里实测这个接口真实连通；已用 Playwright 拦截请求、按接口真实文档格式mock返回值验证了前端的解析/匹配/填表逻辑，接口连通性需要在有正常公网访问的环境（比如你本地）里验证一次。

## 原型范围说明

这是 stage1+2 的融合演示版，用于验证产品方向，非最终生产架构：
- 成分冲突用规则表匹配，不需要接入AI
- 数据持久化用 SQLite 单文件，够用即可，不需要额外的用户系统/鉴权
