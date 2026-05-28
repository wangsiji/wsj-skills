# wsj-miniprogram Bug Patterns

> 完整 bug 模式目录见 `uniapp-miniprogram-optimization` 技能。此文件记录项目特有的修复历史。

## 已修复 Bug 记录（2026-05-14 优化会话）

| Bug | 原因 | 修复 |
|-----|------|------|
| 列表页显示全部而非过滤后 | `v-for="article in freeArticles"` 应为 `v-for="article in filteredArticles"` | 用 filteredArticles |
| `uni is not defined` 运行时错误 | Vue SFC 有两个 `<script>` 块，第二个用 `uni` 但无 import | 删除第二个 `<script>` 块；`uni` 在 uni-app 全局可用 |
| back 按钮无效 | `switchTab({ url: '/pages/index/index' })` 路径不存在 | 确认 tabBar 路径，当前是 `/pages/tools/tools` |
| picker 选不中 | `:value="findIndex(...)"` 找不到时返回 -1 | 用单独的 `selectedIndex` 状态 + fallback |
| `.reduce` 崩溃 | 无数据时为 `undefined` | `(weekRecords[day.key] ?? []).reduce(...)` |
| `Math.max(...[], 1)` 返回 NaN | 空数组展开后 NaN | `arr.length ? Math.max(...arr) : 1` |

## 新发现的 Bug（2026-05-14 第二优化会话）

| Bug | 位置 | 修复 |
|-----|------|------|
| setInterval 内存泄漏 | `report.vue` onMounted 中 setInterval 未在 onUnmounted 清理 | 保存 ID → `onUnmounted` 中 `clearInterval` |
| 6 个子页面 navigateBack 无 fallback | articles/read/report/investment/privacy/agreement | 统一 `goBack()` 含 `switchTab` 兜底 |
| 导航栏样式不一致 | 7 个页面 nav-bar 多种写法 | 统一为 44px / 32×32 盒子返回按钮 / 16px 标题 |
| 付费标签颜色混用 | articles.vue 紫 `#a855f7` vs mine.vue 金 `#fef3c7` | 统一为金色 `#fef3c7 / #92400e` |
| privacy.vue 拼写错误 | "未成人年" → "未成年人" | 修正 |
