---
name: wsj-calculator-mini
description: 富足人生微信小程序开发维护：当用户要求开发/优化「富足人生」微信小程序（FIRE 计算器等工具）时使用。uni-app + Vue3 + TS，项目路径 ~/projects/wsj-miniprogram。覆盖编码、构建、小程序上传。
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wechat-miniprogram, uni-app, vue3, typescript]
    category: dev
---

# 富足人生小程序（路由版 v2）

> 主文件只做路由 + 高频信息（项目/命令/引擎）。搭建细节/优化流程在 `references/`，按需读取。

## 黄金 5 条

1. 先构建确认能编译（`npm run build:mp-weixin`），再排查运行时
2. 修 bug 后必须做数值验证（`node /tmp/test_calc.js` 基准对照）
3. 提交 `src/` + `dist/` 构建产物，不 gitignore dist/
4. 结构性改动 → 直接 `write_file` 完整文件；纯文本替换才用 patch
5. 页面路由在 `pages.json` 注册，末尾不可有 `lazyCodeLoading`（导致 `ref is not defined`）

## Rule Priority（排查时）

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | 编译通过 | 构建不报错再排查运行时；前台模式报错→后台模式 |
| **P1** | 数值正确 | 5 个求解器（FV/PV/PMT/Rate/Years）对标 calculator.net |
| **P2** | 微信规范 | tabBar 首个页面必须在 pages[] 首；避免 v-html SVG（rich-text 白屏） |
| **P3** | Fallback | navigateBack 必须有页面栈检查（`getCurrentPages().length > 1`） |

## Task Router

```
用户说"小程序有问题/改功能/加页面/编译报错"
  ↓
A 编译报错 → 先 npm run build → 看 vite 错误 → pgk.json/路径
B 运行时白屏 → 诊断优先（checklist）→ references/optimization.md
C 修改已有功能 → 定位 src/ 对应文件 → 直接改 → 重新构建
D 加新页面 → 创建 .vue → pages.json 注册 → 构建 → 刷新
E 数值问题 → 看计算引擎（下方）+ 运行 node /tmp/test_calc.js 验证
F 提交/上线 → commit + push + 微信开发者工具上传
```

## 项目信息

- AppID: `wxb6514fa4040c41d8`
- 项目路径: `~/projects/wsj-miniprogram`
- 技术栈: uni-app + Vue 3 + TypeScript
- 构建产物: `dist/build/mp-weixin/`
- 代码模型: DeepSeek

## 计算引擎（5 个求解器）

统一**月复利**计息。周期利率 = `(1 + EAR)^(1 / 每年期数) - 1`（⚠️ 非名义利率 `r/100/compound`）。

| 模式 | 求解 | 函数 | 方法 |
|------|------|------|------|
| `endAmount` | 终值 FV | `calcFV` | 封闭公式 |
| `startAmount` | 初始本金 PV | `calcPV` | 封闭公式 |
| `contribution` | 每期投入 PMT | `calcPMT` | 封闭公式 |
| `rate` | 年化 R | `calcRate` | Newton 法(100次) |
| `years` | 年限 N | `calcYears` | 二分法(0.01-100年) |

数值验证：`node /tmp/test_calc.js`（基准 PV=20000,R=6%,N=10y,PMT=1000→FV=198,290.40）

## 开发命令

```bash
cd ~/projects/wsj-miniprogram
npm install                           # 安装依赖
npm run dev:mp-weixin                 # 开发模式（热更新）
npm run build:mp-weixin               # 生产构建
node_modules/.bin/uni build -p mp-weixin > /tmp/uni_build.log 2>&1 && cat /tmp/uni_build.log  # 后台构建
```

## 目录结构

src/pages/index/index.vue（主页面）+ components/（ModeSelector/InputForm/ResultSummary/PieChart...）+ utils/（calc/validate/format/types）

## Pre-flight Check

- [ ] 编译通过（build 无 error）
- [ ] 内存无 `router-view`（必须 `<slot />`）
- [ ] pages.json pages[0] 是 tabBar 页

## Never Do

- ❌ App.vue 写 `<router-view />`（小程序白屏）
- ❌ pages.json 设 `lazyCodeLoading: "requiredComponents"`（ref is not defined）
- ❌ gitignore `dist/`（构建产物需提交）
- ❌ 结构性改动用 patch（应用 write_file 完整文件）
- ❌ navigateBack 无 fallback（页面栈为 1 时静默失败）

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/setup.md` | 从零搭建：项目初始化/路径约定/SFC命名冲突/pages.json/TabBar |
| `references/optimization.md` | 诊断排查/精简策略/页面结构/常见Bug模式/设计规范 |
| `references/calc-details.md` | 计算引擎细节（EAR vs 名义率陷阱/PITFALL 频率泄漏/SVG 面积图） |
