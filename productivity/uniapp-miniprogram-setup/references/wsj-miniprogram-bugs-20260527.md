# wsj-miniprogram Bug Patterns (2026-05-27 session)

## 新增 Bug 模式

| Bug | 原因 | 修复 |
|-----|------|------|
| articles.vue 有重复 `<script>` 块（第99行） | Options API 块导出 `{ uni: uni }`，Vue SFC 有两个 script | 删除重复块；`uni` 在 uni-app 全局可用 |
| 全部6个子页面 navigateBack 无 fallback | `uni.navigateBack()` 在页面栈空时静默失败 | 统一 `goBack()` 函数含 `switchTab` 兜底 |
| report.vue setInterval 内存泄漏 | `onUnmounted` 未清理 `setInterval` | 保存 timer ID 到变量，`onUnmounted` 中 `clearInterval` |
| privacy.vue "未成人年" 拼写错误 | 应为 "未成年人" | 修正 |
| 付费标签颜色不统一 | articles.vue 用紫色 (#a855f7)，mine.vue 用金色 | 统一为金色 `#fef3c7 / #92400e` |
| 导航栏样式6个页面各不同 | 无统一规范，font-size/颜色/padding 各异 | 统一为 32×32 盒子返回按钮 + 44px 高度 + border-bottom |

## goBack 统一模式

所有非 tabBar 页面都需要，差异只在 `switchTab` 目标：
- 工具类子页面 → `/pages/tools/tools`
- 内容类子页面 → `/pages/mine/mine`

```ts
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.switchTab({ url: '/pages/tools/tools' })
  }
}
```

## 统一导航栏 CSS

```css
.nav-bar { height: 44px; display: flex; align-items: center; padding: 0 12px; gap: 8px; border-bottom: 1px solid #161618; }
.back-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: #141416; border: 1px solid #1e1e22;
  border-radius: 8px; font-size: 20px; color: #fafafa;
}
.nav-title { font-size: 16px; font-weight: 700; color: #fafafa; }
```

## 2026-05-28 Session 新增 Bug 模式

| Bug | 原因 | 修复 |
|-----|------|------|
| SVG `<line>` 渲染报错 "Duplicate attribute" | Vue 模板中 line 元素同时有 `:y1` 和 `:y1`（应为 `:y1` + `:y2`） | 改第二 个为 `:y2` |
| 复利计算 `n=1` 时 contributions 全按月累加 | 固定每月投 `C`，但 n=1 应每期（每年）投 `C×12` | 按 `monthsPerPeriod = 12/n` 缩放每期投入金额 |
| schedule label 全部相同 | label 三元表达式两个分支文字一样 | 根据复利频率 n 分别生成月/季度/半年/年 label |
| v-html 渲染 SVG Y轴标签错位 | `yLabels.split('</text>').filter(Boolean)` 拼接时多出 `</text>` | 直接用 `v-for` 渲染标签数组，不过 DOM |
| 微信构建报 "uni-app 有新版本" | 只是提示不是错误，忽略即可 | 构建成功看 `DONE Build complete` 即可 |

### 复利计算核心逻辑（已验证正确）

```
n = 每年复利次数（1/2/4/12）
monthsPerPeriod = 12 / n
periodRate = r / n
totalPeriods = n × t

每期投入 = C × monthsPerPeriod（期初或期末）
balance = balance × (1 + periodRate) + 期投入
```

公式验证（起始20000 + 1000/月 + 6% + 10年 + 每月复利）：
- 本金终值：36,387.93
- 定投终值：163,879.35
- 总终值：200,267.28
- 利息：60,267.28
- 增长倍数：1.43

## 受影响页面

| 文件 | goBack 目标 | 原问题 |
|------|------------|--------|
| articles/articles.vue | `/pages/mine/mine` | 重复 script 块 + goBack 无 fallback |
| articles/read.vue | `/pages/mine/mine` | 2处 navigateBack 无 fallback |
| timebox/report.vue | `/pages/tools/tools` | 内存泄漏 + navigateBack 无 fallback |
| tools/investment.vue | `/pages/tools/tools` | navigateBack 无 fallback |
| mine/privacy.vue | `/pages/mine/mine` | 拼写错误 + navigateBack 无 fallback |
| mine/agreement.vue | `/pages/mine/mine` | navigateBack 无 fallback |
