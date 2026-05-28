# UniApp 微信小程序 UI 设计规范

## 设计原则

深色主题优先。界面传给用户前必须自检确认没问题，不要说"试试看"。

---

## 颜色系统

### 背景色阶
| 用途 | 色值 |
|------|------|
| 页面背景 | `#0a0a0f` |
| 卡片/容器 | `#141416` |
| 边框/分割线 | `#1e1e22` |
| 次级边框 | `#27272a` |

### 文字色阶
| 用途 | 色值 |
|------|------|
| 主文字 | `#fafafa` |
| 次要文字 | `#a1a1aa` |
| 辅助文字 | `#71717a` |
| 禁用/占位 | `#52525b` |
| 深禁用 | `#3f3f46` |

### 语义色
| 用途 | 色值 |
|------|------|
| 主色调（按钮/高亮） | `#6366f1`（紫色） |
| 成功/收益 | `#22c55e` |
| 警告 | `#f59e0b` |
| 危险/停止 | `#ef4444` |

### 标签色
```
免费: 背景 #d1fae5 / 文字 #065f46
付费: 背景 #fef3c7 / 文字 #92400e
```

---

## 字体规范

```css
font-family: -apple-system, BlinkMacSystemFont, sans-serif;
```

字号层级：
- 计时器大数字: 64px / 800
- 大标题: 26px / 800
- 导航栏标题（nav-title）: 16px / 700（统一标准化）
- 卡片标题: 20px / 800
- 正文: 15px / 600
- 辅助说明: 13px / 400 或 500
- 标签/元信息: 10-12px / 500

---

## 圆角规范

| 元素 | 圆角 |
|------|------|
| 页面卡片 | 16px |
| 按钮/输入框/单元格 | 12px |
| 小标签/徽章 | 8px 或 20px（药丸形） |
| 图标容器 | 14px |
| 头像容器 | 10px |

---

## 间距规范

- 页面横向边距: 20px
- 卡片内边距: 16-20px
- 元素间距（gap）: 8-16px
- section 间距: 20-24px

---

## 组件模式

### 工具卡片（tools.vue）
```
背景: linear-gradient(135deg, 深色1 0%, 深色2 100%)
装饰圆: 右上角，半透明小圆，制造层次感
结构: icon容器 + badge + 标题 + 描述 + 底部CTA行
```

### 文章卡片（articles）
```
封面: 160px高，渐变背景 + emoji居中（不用真实图片URL）
标签: 免费/付费 彩色小标签右上角
结构: 封面图 + 标题行（标题+标签） + 描述 + 元信息
```

### 时间盒计时器（v2 — 线性进度条）
```
数字显示: 64px / 800 tabular-nums
进度条: 220px宽 × 4px高，圆角2px，背景 #1e1e22
进度填充: #6366f1 → #818cf8（激活态），过渡 0.5s cubic-bezier
时长胶囊: 52px宽，选中态 #1e1b4b 背景 + #6366f1 边框
激活态发光: box-shadow 0 0 12px rgba(99,102,241,0.5)
完成弹窗: 毛玻璃 backdrop-filter blur(8px)，卡片 popIn 弹性动画
```

### 复利计算器（v2 — 堆叠柱状图）
```
Tab 切换: 胶囊按钮，active 态 #6366f1
表单: 行内输入 + 单位后缀（元/年/%），右对齐
堆叠柱状图: SVG stacked bars（本金#3b82f6/投入#6366f1/收益#22c55e）
年度表: flex 表格，列宽 40px 年份 + flex:1 数值列
结果大数字: 40px / 800，下方比例分解条（break-bar）
```

### 翻页时钟
```
全屏深色: background #050508 + radial-gradient 中心光晕
数字卡: 80×120px，渐变背景，顶部光泽线，阴影深度/内发光
秒数卡: 56×80px，opacity 0.6（层级区分）
分隔点: 6px 圆点，#6366f1，呼吸动画（dotPulse 2s）
导航栏: 3秒自动隐藏，轻触唤出，backdrop-filter + rgba 背景
```

### 自定义导航栏（所有子页面统一）
```css
.nav-bar { height: 44px; display: flex; align-items: center; padding: 0 12px; gap: 8px; border-bottom: 1px solid #161618; }
.back-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: #141416;
  border: 1px solid #1e1e22;
  border-radius: 8px;
  font-size: 20px; color: #fafafa;
}
.nav-title { font-size: 16px; font-weight: 700; color: #fafafa; }
```
> 更多规范见 `uniapp-miniprogram-optimization` 技能。

---

## Bug 记录

### todayIdx 周柱状图错位

**现象**: 周日（getDay()=0）时今日列定位到周三位置。

**原因**: `getDay()` 返回 0=周日，但数组索引 0=周一。

**修复**:
```ts
const todayIdx = new Date().getDay()
// ❌ 错: idx=0 时周日在数组第6位
// ✓ 对:
const todayColIdx = todayIdx === 0 ? 6 : todayIdx - 1
```

---

### articles/read.vue 重复 script 块

**现象**: 构建报 `<script> duplicate` 相关警告。

**原因**: Vue SFC 同时存在 `<script setup>` 和旧版 Options API `<script>` 块。

**修复**: 删除 Options API `<script>` 块，只保留 `<script setup lang="ts">`。

---

### 封面图用真实 URL 会失效

**原则**: 不用外部图片 URL 做占位图，改用 emoji + 渐变背景。

```vue
<view class="article-cover" :style="{ background: 'linear-gradient(135deg, #1a1a2e, #16213e)' }">
  <text style="font-size: 48px">{{ emoji }}</text>
</view>
```