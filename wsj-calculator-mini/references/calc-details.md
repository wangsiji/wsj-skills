---
name: wsj-miniprogram-calc-details
description: 计算引擎细节——EAR vs 名义利率陷阱、频率泄漏、PITFALL记录、SG面积图。
---

### 计算引擎

#### 核心原理

统一**月复利**计息，但定投频率可变。每个频率的周期利率由年化收益率（EAR）换算：

```
周期利率 = (1 + EAR)^(1 / 每年期数) - 1
```

⚠️ **EAR vs 名义利率陷阱**：calculator.net 和大多数金融计算器使用**有效年利率（EAR）**。给定年利率 r%，每期利率 = `(1 + r/100)^(1/compound) - 1`，**不是** `r/100/compound`。后者是名义利率，在当前利率下误差约 2.6%（月复利时：0.5% vs 0.4868%）。

#### 5 种模式

| 模式 | 标签 | 求解目标 | 定投频率 |
|------|------|---------|---------|
| `endAmount` | 养老金 | 终值 FV | 每周 / 每月 / 每年 |
| `startAmount` | 初始额 | 初始本金 PV | 无 |
| `contribution` | 定投额 | 每期投入 PMT | 每周 / 每月 / 每年 |
| `rate` | 收益率 | 年化收益率 R | 每周 / 每月 |
| `years` | 年限 | 投资年限 N | 每周 / 每月 |

PITFALL — 模式切换时的频率泄漏（通用）：ModeSelector 用 v-model 只更新 activeMode，不触发 form 更新。从其他模式切到有不同频率选项的模式时，`form.contribFreq` 可能保留旧值。`calculate()` 中用 `const sFreq = freq || 'monthly'` 做兜底，但若旧值恰好是合法值（如 'yearly'），兜底无效。**修复模式**：对于有特定频率要求的模式，在 `calculate()` 分支内显式声明频率，不依赖 `sFreq`。定投额模式已改为用户可选频率（每周/每月/每年），`InputForm` 显示频率选择但隐藏金额输入，结果卡片同时显示每年/每月/每周三行，通过所选频率的 PMT 归一化换算。

PITFALL — 定投额结果多行展示的归一化陷阱：结果卡片三行（每年/每月/每周）必须从**统一月均基准**推导。`solvedValue` 是按所选频率的每期 PMT（选年则值是年额、选月则月额、选周则周额），直接放入"每月"行会出错。正确做法：先归一化 → `normMonthly = freq='yearly' ? solvedValue/12 : freq='weekly' ? solvedValue*52/12 : solvedValue`，再 `fmtYearly = normMonthly*12`、`fmtWeekly = normMonthly*12/52`。

#### 求解器

| 函数 | 方法 | 说明 |
|------|------|------|
| `calcFV` | 封闭公式 | PV、PMT、r、n → 终值 |
| `calcPV` | 封闭公式 | FV、PMT、r、n → 本金 |
| `calcPMT` | 封闭公式 | PV、FV、r、n → 每期投入 |
| `calcRate` | Newton 法 | 导数逼近，100 次迭代 |
| `calcYears` | 二分法 | 搜索区间 0.01–100 年 |

所有公式已对标 calculator.net 基准数据验证。**修完 bug 后必须做数值验证**：

```bash
node /tmp/test_calc.js
# 基准：PV=20000, R=6%, N=10y, PMT=1000, 月末 → FV=198,290.40
```

#### SG 面积图（v-html 渲染）

⚠️ **SVG `<line>` 元素禁止重复属性**：Vue 模板中用 `v-for` 渲染多条 line 时，两个端点坐标必须分别用 `:y1` + `:y2`，不能给同一元素绑定两次 `:y1`。

```ts
// 错误 ❌ — Duplicate attribute y1
<line :x1="padX" :y1="..." :x2="W" :y1="..." ... />

// 正确 ✓
<line :x1="padX" :y1="..." :x2="W" :y2="..." ... />
```

### 常见问题

- **npm install peer dependency warnings**：不用管
- **vite build 前台模式报错**：必须用后台模式
- **编译报 "Unexpected token"**：通常是 Vue 模板里的语法错误，从可疑函数逐段注释排查
- **小程序不显示内容**：检查 `pages.json` 的 `globalStyle.navigationStyle` 是否设为 `custom`

---

## 二、项目搭建（Setup）

从零开始搭建 UniApp + Vue3 项目，输出微信小程序。

