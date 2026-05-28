---
name: uniapp-miniprogram-optimization
description: uni-app 微信小程序开发优化 — 单一功能精简策略、页面增删改、dist/git 工作流、设计规范
triggers:
  - "优化小程序"
  - "小程序有 bug"
  - "小程序上线"
  - "miniprogram"
  - "微信小程序"
---

# uni-app 微信小程序开发流程

## 当前项目状态

复利计算器（2026-05-19 全面重构）：6 组件拆分 + TVM 五模式求解器。

项目路径：`/home/wangsiji/projects/wsj-miniprogram`

目录结构（重写后）：
```
src/
├── App.vue              # 启动屏
├── main.ts              # 入口
├── manifest.json
├── pages.json           # 单页注册（navigationStyle: custom）
├── pages/index/
│   └── index.vue        # 主页面（~220行，组装6个组件）
├── components/
│   ├── ModeSelector.vue    # 5模式标签页
│   ├── InputForm.vue       # 动态表单（按模式显隐字段）
│   ├── ResultSummary.vue   # 四格摘要卡
│   ├── PieChart.vue        # SVG 饼图
│   ├── YearlySchedule.vue  # 年度累积表（可折叠）
│   └── MonthlySchedule.vue # 月度累积表（可折叠）
└── utils/
    ├── calc.ts          # TVM五模式求解器 + 年度/月度明细生成
    ├── types.ts         # 类型定义 + 复利选项常量
    ├── format.ts        # 数值格式化
    └── validate.ts      # 表单校验
```

### uni-app import 路径约定（重要）

```ts
// 从 src/pages/index/index.vue：
import { calcFV } from '../../utils/calc'
import ModeSelector from '../../components/ModeSelector.vue'

// 从 src/components/Xxx.vue：
import type { CalcMode } from '../utils/types'
import { fmt } from '../utils/format'
```

> ⚠️ 路径层级错误是编译失败的第一常见原因。`pages/index/` 到 `src/` 需要 `../../`，`components/` 到 `src/` 需要 `../`。

### Vue SFC 命名冲突

当组件名与类型接口名相同时（如 `ResultSummary` 既是组件又是 interface），用别名导入：

```ts
// index.vue
import ResultSummary from '../../components/ResultSummary.vue'
import type { ResultSummary as IResultSummary } from '../../utils/types'

const resultSummary = ref<IResultSummary | null>(null)
```

### defineEmits 只能调用一次

Vue 3 SFC 中 `defineEmits` 只能调用一次，且必须在所有使用 `emit` 的函数之前声明。不要在同一个 `<script setup>` 中调用两次 `defineEmits`。

**Build 验证**（每次修改后必跑）：
```bash
cd /home/wangsiji/projects/wsj-miniprogram && npm run build:mp-weixin
```
输出：`dist/build/mp-weixin/`（导入微信开发者工具）

微信开发者工具导入路径：`/home/wangsiji/projects/wsj-miniprogram/dist/build/mp-weixin`

## 精简策略：删除多余页面

当需要把多页面应用精简为单页面时，执行顺序不能乱：

1. **修改 `pages.json`**：只保留目标页面，删除 tabBar 配置（无 tabBar 时不写 `tabBar` 字段）
2. **迁移页面文件**：`mv src/pages/原路径/page.vue src/pages/新路径/page.vue`
3. **修改 `App.vue`**：去掉 tabBar 相关内容，启动屏文字改掉，删除 pinia（无全局状态时）
4. **删除无用依赖**：`pinia`、`utils/`、`constants/`、`static/tabbar/`（先确认无 import）
5. **修改 `manifest.json`**：`name` 和 `description` 同步更新
6. **添加 `.gitignore`**：确保 dist 不进版本控制
7. **构建验证**：`npm run build:mp-weixin`
8. **git commit**：只提交 `src/` 和 `.gitignore`，**不要提交 dist/**

### ⚠️ dist/ 的 git 陷阱

**问题**：`npm run build:mp-weixin` 会覆盖整个 `dist/build/mp-weixin/`。如果 dist 已在 git 里，每次 build 会产生大量 D 文件（删除旧文件）+ M 文件（更新残留文件），git 历史会被 dist 污染。

**解决方案**：
```bash
# 项目首次清理：在 .gitignore 加入后
git rm -r --cached dist/     # 停止跟踪 dist/
git add .gitignore src/       # 只提交源码
```

**每次构建后验证**：
```bash
git status dist/  # 应该没有变化
```

**确认 .gitignore 正确**：
```
node_modules/
dist/
*.log
.DS_Store
```

## 页面结构规范

### 启动屏（App.vue）
uni-app 用 `<slot />` 作为页面渲染出口（**不要用 `<router-view />`**，那是 Vue Router 的组件，微信小程序里不存在，用了会导致 `Error: timeout` 白屏）。

对于不需要启动动画的场景（启动屏纯 CSS fade-out），直接删除 `<slot />`：

```vue
<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { ref } from 'vue'

const ready = ref(false)

onLaunch(() => {
  // CSS 动画自动结束，无需 setTimeout 阻塞
  ready.value = true
})
</script>

<template>
  <view class="app">
    <view class="splash" :class="{ hide: ready }">
      <view class="splash-inner">...</view>
    </view>
    <!-- 单页面应用：uni-app 框架直接渲染 page，不需要 router-view 也不强制需要 slot -->
  </view>
</template>
```

**不要在 App.vue 写 `<router-view />`**，也不要写 `<slot />`（单页面应用不需要显式 slot，uni-app 框架直接渲染 page）。

### 全局样式（App.vue）
```css
page {
  background-color: #0a0a0f;
  color: #e4e4e7;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
}
button::after { border: none; }  /* 去小程序按钮边框 */
::-webkit-scrollbar { display: none; }
```

## 诊断先行

用户说"小程序有问题/测试不成功"时，**先全面审查再动手**，不要只盯着报错日志。按以下顺序系统排查：

```bash
# 0. 先构建确认能编译
cd /home/wingsiji/projects/wsj-miniprogram && npm run build:mp-weixin

# 0.5. 检查 build 产物是否是最新的（日期对比）★★ 本次 Debug 根因 ★★
# 如果 dist/build 的文件日期早于 src/ 修改日期 = 开发者工具在用旧 build
stat dist/build/mp-weixin/app.js | grep Modify
stat src/pages/index/index.vue | grep Modify
# 如果 app.js 比 index.vue 还旧 → 重新导入项目到开发者工具

# 1. pages.json 注册完整性 — 所有 src/pages/** 的 .vue 是否都已注册？
find src/pages -name '*.vue' | while read f; do
  p=$(echo "$f" | sed 's|src/||;s|\.vue$||')
  grep -q "$p" src/pages.json || echo "❌ 未注册: $p"
done

# 2. v-html + SVG — 小程序 rich-text 不支持 SVG，图表会白屏
grep -rn 'v-html' src/ && echo "⚠️ 检查是否有 SVG v-html"

# 3. goBack() fallback — 跳转目标是否有效
grep -rn 'navigateBack\|switchTab' src/

# 4. tabBar 配置 — pages.json 是否有 tabBar？tab 图标是否存在？
grep -A5 'tabBar' src/pages.json

# 5. App.vue — 用 <slot /> 而非 <router-view />
grep 'router-view' src/App.vue && echo "❌ 必须用 <slot />"

# 6. 孤立文件 — 有没有 .ts 文件是纯文本/未引用？
grep -rn 'tao-te-ching\|import.*from.*utils' src/ --include='*.vue' --include='*.ts'
```

常见问题优先级：
- **P0 阻塞**：页面未注册、v-html+SVG、App.vue 用了 `<router-view />`
- **P1 功能缺失**：goBack fallback 指向不存在页面、tabBar 未配置
- **P2 代码质量**：.ts 文件是纯文本、未引用的工具文件

## 常见 Bug 模式（单页面应用）

### 1. navigateBack 无 fallback
**症状**：页面栈只有1个时 `uni.navigateBack()` 静默失败。

```ts
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/index/index' })
}
```

### 2. template 拼写/语法错误
- `{{ article.author}}` 多余空格（}} 前有空格）→ `{{ article.author }}`
- 动态 class 写成 `:class="'today'"` 而非 `:class="{ 'today': condition }"`

### 3. 重复 `<script>` 块
**检测方法**：搜索 `<script` 出现次数 > 1 的 Vue 文件。

### 4. `@click` 内联注释导致构建失败
```vue
<!-- ✗ 构建失败 -->
<view @click="/* toggle */">
<!-- ✓ 正确 -->
<view @click="toggle">
```

### 5. `v-html` 注入 SVG — touch 事件不生效（SVG 本身正常渲染）

**⚠️ 修正**：之前描述"SVG 完全不显示"是错误的。实测 SVG 通过 `rich-text` 可以正常渲染，**问题仅在于** `v-html` 字符串中内联的 touch 事件处理器（`@touchstart`、`@touchmove`、`@touchend`）不生效。微信小程序的 `<rich-text>` 组件支持 SVG 标签（text、path、line、circle、rect 等），但不支持元素级事件绑定。

**症状**：十字光标 touch 交互（曲线图上的触摸点显示 tooltip）在真机上完全无反应。

**根因**：SVG 模板字符串里写了 `@touchstart="onCompareTouch"` 等事件，但 `rich-text` 编译后不处理这些事件绑定。

**修复方案 A**（首选 — 本次验证通过）：父容器捕获 touch 坐标，组件级处理

```vue
<!-- 错误：touch 事件写在 SVG 字符串里，rich-text 不解析 -->
<view class="chart-wrap" v-html="compareSvg"/>

<!-- 正确：touch 事件绑在父容器，用 currentTarget 获取 SVG 外层容器坐标 -->
<view class="chart-wrap"
  @touchstart="onCompareTouch"
  @touchmove="onCompareTouch"
  @touchend="onCompareEnd">
  <rich-text :nodes="compareSvg" />
</view>
```

```ts
// touch 事件处理器 — 绑在外层 view 上，用 currentTarget 取容器 rect
function onCompareTouch(e: any) {
  const touch = e.touches ? e.touches[0] : e.detail
  const wrapEl = e.currentTarget as HTMLElement   // 不是 target（SVG内部元素），而是外层容器
  if (!wrapEl) return
  const rect = wrapEl.getBoundingClientRect()
  const { years: t } = form.value
  const chartW = CHART_W - PAD_L - PAD_R
  const relX = touch.clientX - rect.left
  const ratio = Math.max(0, Math.min(1, (relX - PAD_L) / chartW))
  touchYear.value = Math.round(ratio * t)
}

function onCompareEnd() {
  touchYear.value = -1
}
```

**注意**：`clientX/Y` 在微信小程序中需要确认 — 若不生效，微信的 touch 事件对象结构是 `e.detail`（模拟事件）或 `e.touches[0]`（原生触摸），两者都有 `clientX/clientY`。

**修复方案 B**：WXML flex 柱状图（适合堆叠柱，不适合曲线）
方案 B 仍然有效（flex 柱状图 + 对比表），但方案 A 更简洁，曲线图交互完全保留。

详见：`references/wxml-chart-patterns.md`
### 7. `lazyCodeLoading: "requiredComponents"` 导致生产环境 `ref is not defined`
**症状**：开发工具正常，提交体验版后 `ReferenceError: ref is not defined`（app.js setup 函数内）。

**根因**：`pages.json` 配置 `"lazyCodeLoading": "requiredComponents"` 后 vendor.js 以分包懒加载。app.js 模块级 `ref()` 调用在 vendor.js 加载完成前执行。开发工具因预加载行为而正常，生产环境才触发。

**修复**：从 `pages.json` 删除 `lazyCodeLoading` 字段（单页应用不需要此优化）：
```json
{
  "pages": [...],
  "globalStyle": {...}
  // 不写 "lazyCodeLoading": "requiredComponents"
}
```

### 8. Syncthing 设备无法连接（device sync，非 web GUI）

**症状**：用户通过设备 ID 连接 Syncthing 失败（不是 web GUI 8384 端口问题）。

**排查顺序**：
1. `ps aux | grep syncthing` — 进程是否存在
2. `ss -tlnp | grep -E '22000|8384'` — 同步端口(22000)和 GUI 端口(8384)是否监听
3. **不要先查 8384 web GUI**，用户用的是 device sync 协议，走 22000 端口
4. 检查云服务器安全组是否开放 22000（同步端口）

**修复**：
```bash
# 清理残留进程
pkill -9 -f syncthing
sleep 2

# 用 systemd 管理（Restart=always 自动拉起）
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/syncthing.service << 'EOF'
[Unit]
Description=Syncthing

[Service]
ExecStart=/usr/local/bin/syncthing serve --no-browser --no-restart --gui-address=127.0.0.1:8384 --home=/var/syncthing
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable syncthing
systemctl --user start syncthing
```

**确认 lingering 已开启**（VPS 重启后用户服务自启）：
```bash
loginctl show-user wangsiji | grep Linger  # 应输出 Linger=yes
```

**GUI 只监听本地**：上例中 `--gui-address=127.0.0.1:8384` 只允许本机访问 GUI，外部无法访问（安全），但同步功能(22000)不受影响。

### 9. App.vue 使用 `<router-view />` 导致 `Error: timeout` 白屏
**症状**：开发者工具编译超时、白屏，Console 报 `Error: timeout` 或 WAServiceMainContext 超时。App.vue 内容完全空白。

**根因**：`<router-view />` 是 Vue Router 组件，在微信小程序运行环境中不存在。小程序没有 Vue Router，App.vue 使用 `<router-view />` 后渲染失败导致超时。

**症状识别**：
```bash
# app.wxml 不存在（正确应该有）
ls dist/build/mp-weixin/app.wxml  # 应报错 "No such file"
# app.js 里有 router-view 的残留代码
grep 'router-view' dist/build/mp-weixin/app.js
```

**修复**：App.vue 用 `<slot />` 替代：
```vue
<template>
  <view class="app">
    <slot />
  </view>
</template>
```

**为什么不是 `<router-view />`**：uni-app 的 Vue 3 版本中，App.vue 是应用根组件，不负责路由。页面内容通过 `<slot />` 由 uni-app 框架注入，App.vue 只需要提供全局样式和布局容器。

### 7. 开发者工具 Timeout / 长时间白屏
**症状**：`Error: timeout` 或 WAServiceMainContext 超时。

**排查顺序**：
1. **清缓存**：开发者工具 → 清缓存 → 清除全部缓存 → 重新编译
2. **确认导入路径**：用 `dist/build/mp-weixin/`（build 产物），不要用 `dist/dev/mp-weixin/`
3. **检查 `app.js` require 链**：
   ```bash
   # vendor.js 必须有 ref export
   grep 'exports.ref' dist/build/mp-weixin/common/vendor.js
   # app.js 必须 require vendor.js
   head -2 dist/build/mp-weixin/app.js
   ```
4. **确认 pages.json 无 `lazyCodeLoading`**（同上第6条）
5. **检查 project.config.json 的 appid 是否正确**

**验证 build 产物完整性**：
```bash
ls dist/build/mp-weixin/
# 必须有：app.js app.json App.wxml common/vendor.js pages/
```

## 设计规范

### 导航栏统一规范
- 返回按钮：32×32 卡片背景（`background: #141416; border: 1px solid #1e1e22; border-radius: 8px`），文字 `‹`（font-size 20px，color `#fafafa`）
- 导航栏：`height: 44px; padding: 0 20px; border-bottom: 1px solid #161618`
- 标题：font-size 16px，font-weight 700，颜色 `#fafafa`

```css
.nav-bar { height: 44px; display: flex; align-items: center; padding: 0 20px; border-bottom: 1px solid #161618; }
.back-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: #141416; border: 1px solid #1e1e22;
  border-radius: 8px; font-size: 20px; color: #fafafa;
}
.nav-title { font-size: 16px; font-weight: 700; color: #fafafa; margin-left: 8px; }
```

### SVG 图表渲染（compareSvg / chartSvg）
两种独立 computed 渲染器，避免相互干扰：
```ts
// 复用计算逻辑提取为独立函数
function fvAtYear(rate: number, year: number) { ... }

const compareSvg = computed(() => { ... })  // 对比曲线
const chartSvg = computed(() => { ... })   // 堆叠柱状图
```

### 类型与工具规范化（2026-05 重构）

单文件计算器重构时的标准结构：

**`src/utils/types.ts`** — 所有业务类型定义（2026-05 追加 ValidationError）：
```ts
export interface FormData {
  startAmount: number
  years: number
  rate: number
  compound: number           // 复利频率：1=年,2=半年,4=季,12=月,365=日,0=连续
  monthlyContrib: number
  contributeTime: 0 | 1     // 0=期末, 1=期初
  targetEnd: number
}

export interface ResultSummary {
  endBalance: number
  startAmount: number
  totalContrib: number
  totalInterest: number
}

export interface YearlyRow { year: number; deposit: number; interest: number; balance: number }
export interface MonthlyRow { month: number; deposit: number; interest: number; balance: number }

export interface CompoundOption { value: number; label: string }
export const COMPOUND_OPTIONS: CompoundOption[] = [
  { value: 1, label: '每年' }, { value: 12, label: '每月' }, // ...
]
```

**`src/utils/calc.ts`** — TVM 五模式求解器（2026-05-19 重写，对标 calculator.net）：
```ts
// ⚠️ 关键：EAR→周期利率，不是名义利率
function periodicRate(rPct: number, compound: number): number {
  const ear = rPct / 100
  if (compound === 0) return ear
  if (ear === 0) return 0
  return Math.pow(1 + ear, 1 / compound) - 1
  // 例如：6% EAR，月复利 → (1.06)^(1/12)-1 = 0.4868%，不是 6%/12=0.5%
}

export function calcFV(PV, rPct, compound, years, PMT, type): number  // 终值
export function calcPV(FV, rPct, compound, years, PMT, type): number  // 本金
export function calcPMT(PV, FV, rPct, compound, years, type): number  // 定投
export function calcRate(PV, FV, years, compound, PMT, type): number  // 收益率（Newton法）
export function calcYears(PV, FV, rPct, compound, PMT, type): number  // 年限（二分法）
export function genYearlySchedule(...): YearlyRow[]   // 年度明细
export function genMonthlySchedule(...): MonthlyRow[] // 月度明细

// 验证基准：PV=20000, EAR=6%, N=10y, 月投1000, 月末 → FV=198290.40
```

> ⚠️ **EAR vs 名义利率陷阱**：calculator.net 和大多数金融计算器使用 **有效年利率（EAR）**。给定年利率 r%，每期利率 = `(1 + r/100)^(1/compound) - 1`，**不是** `r/100/compound`。后者是名义利率，在当前利率下误差约 2.6%（月复利时：0.5% vs 0.4868%）。

**`src/utils/validate.ts`** — 表单校验（返回 ValidationError[]，UI 显示红色提示）

### touch 事件性能优化（对比曲线图）

**问题**：touchmove 时每帧都修改 `touchYear.value`，导致 `compareSvg` computed 全量重算（SVG 字符串 + 重新渲染），低端机卡顿。

**修复**：局部变量暂存，touchend 才提交到响应式：
```ts
let _pendingYear = -1

function onCompareTouch(e: any) {
  const touch = e.touches ? e.touches[0] : e.detail
  const wrapEl = e.currentTarget as HTMLElement
  if (!wrapEl) return
  const rect = wrapEl.getBoundingClientRect()
  const { years: t } = form.value
  const chartW = CHART_W - PAD_L - PAD_R
  const relX = touch.clientX - rect.left
  const ratio = Math.max(0, Math.min(1, (relX - PAD_L) / chartW))
  _pendingYear = Math.round(ratio * t)
  // 不在这里设置 touchYear.value，避免 compareSvg 高频重算
}

function onCompareEnd() {
  touchYear.value = _pendingYear
  _pendingYear = -1
}
```

### 表单校验模式（2026-05 重构）

**旧模式（错误）**：`validateForm()` 直接修改 `form.value`，用户完全无感知输入被篡改。

**新模式（正确）**：返回 ValidationError 列表，UI 显示红色错误提示：
```ts
function validateForm(): boolean {
  const errors: ValidationError[] = []
  const { startAmount, years, rate, monthlyContrib, targetEnd } = form.value
  if (isNaN(startAmount) || startAmount < 0) errors.push({ field: 'startAmount', message: '本金需≥0' })
  if (isNaN(years) || years <= 0 || years > 100) errors.push({ field: 'years', message: '年限需在1-100之间' })
  if (isNaN(rate) || rate < 0 || rate > 100) errors.push({ field: 'rate', message: '年利率需在0-100%' })
  // ...
  validationErrors.value = errors
  return errors.length === 0
}
```

对应的 error-bar UI（红色提示栏）：
```vue
<view class="error-bar" v-if="validationErrors.length > 0">
  <text v-for="err in validationErrors" :key="err.field">{{ err.message }}</text>
</view>
```

```css
.error-bar { background: #3f1e1e; border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #f87171; display: flex; flex-direction: column; gap: 4px; }
```

### 代码质量优先级框架

| 优先级 | 类别 | 示例 |
|--------|------|------|
| P0 | 性能/阻塞/bug | touchmove 节流、重复公式消除、静默修改输入 |
| P1 | 轻微性能/类型安全 | 冗余计算、any 类型参数 |
| P2 | 可维护性 | 魔法数字命名、空 lifecycle hook、未引用文件 |

**组件内使用**：
```ts
import { fmt, fmtInt, fmtChartY, CHART_W, CHART_H, ... } from '../../utils/format'
import type { FormData, CalcResult, ScheduleRow } from '../../utils/types'
import { COMPOUND_OPTIONS } from '../../utils/types'

// 替换所有 ref<any>
const result = ref<CalcResult | null>(null)
const schedule = ref<ScheduleRow[]>([])

// 替换 compoundLabels/compoundKeys 硬编码
const compoundLabels = Object.fromEntries(COMPOUND_OPTIONS.map(o => [o.value, o.label]))
const compoundKeys = COMPOUND_OPTIONS.map(o => o.value)
```

## 上线前检查清单

- [ ] Build 无报错：`npm run build:mp-weixin`
- [ ] .gitignore 覆盖 dist/
- [ ] 返回按钮有 goBack fallback
- [ ] 无 template 拼写错误（多余空格、}} 错位）
- [ ] 无重复 `<script>` 块
- [ ] 导航栏样式统一
