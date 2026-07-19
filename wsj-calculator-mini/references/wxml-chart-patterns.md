# WXML 图表模式 — 微信小程序可用替代方案

## 问题
微信小程序不支持元素级事件绑定（`@touchstart` 等）在 `rich-text` 渲染的 SVG 上生效。SVG 标签本身可以通过 `rich-text` 正常渲染，但 touch 事件写在 SVG 字符串里会被忽略。

## 已验证方案：SVG + rich-text + 父容器 touch 捕获

SVG 通过 `<rich-text :nodes="svgString">` 可以正常渲染。十字光标等 touch 交互通过**父容器**绑定事件处理函数实现。

详见 SKILL.md 完整修复方案 A。

## 方案 B：Flex 柱状图（适合无 touch 交互需求的柱状图）

### 堆叠多色柱状图
```vue
<script setup lang="ts">
const barData = computed(() => {
  const maxV = Math.max(...schedule.value.map(r => r.balance), 1)
  return schedule.value.map(row => ({
    year: row.year,
    balancePct: (row.balance / maxV) * 100,
    depositPct: (row.deposit / maxV) * 100,
    interestPct: (row.interest / maxV) * 100,
    principalPct: ((row.balance - row.deposit - row.interest) / maxV) * 100,
  }))
})
</script>

<template>
  <view class="bar-chart">
    <view v-for="b in barData" :key="b.year" class="bar-column">
      <view class="bar-stack" :style="{ height: b.balancePct + '%' }">
        <view class="bar-interest" :style="{ flex: b.interestPct }"/>
        <view class="bar-contrib" :style="{ flex: b.depositPct }"/>
        <view class="bar-principal" :style="{ flex: b.principalPct }"/>
      </view>
      <text class="bar-year-label">{{ b.year }}</text>
    </view>
  </view>
</template>

<style>
.bar-chart { display: flex; align-items: flex-end; height: 180px; gap: 2px; padding: 0 2px; }
.bar-column { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.bar-stack { width: 100%; max-width: 24px; display: flex; flex-direction: column-reverse; border-radius: 3px 3px 0 0; overflow: hidden; min-height: 2px; }
.bar-principal { background: #3b82f6; min-height: 0; }
.bar-contrib { background: #6366f1; min-height: 0; }
.bar-interest { background: #22c55e; min-height: 0; }
.bar-year-label { font-size: 10px; color: #52525b; margin-top: 4px; }
</style>
```

关键点：
- `flex-direction: column-reverse` 让柱状图从底部向上堆叠
- 每层 `flex: <百分比>` 控制相对高度占比
- 外容器 `height: <百分比>` 控制柱子的总高度
- `min-height: 0` 防止 flex 子元素溢出

## 方案 B：里程碑对比表（替代曲线图）

```vue
<template>
  <view class="compare-bars">
    <view v-for="(yr, yi) in milestoneYears" :key="yr" class="compare-bar-row">
      <text class="compare-year">{{ yr }}年</text>
      <view class="compare-bar-track">
        <view
          v-for="c in compareData" :key="c.rate"
          class="compare-bar-seg"
          :style="{ width: c.values[yi].pct + '%', background: c.color }"
        />
      </view>
    </view>
  </view>
  <!-- 数值表 -->
  <view class="compare-table">
    <view class="sch-header">
      <text class="sch-year">年份</text>
      <text v-for="c in compareData" :key="c.rate" class="sch-num" :style="{ color: c.color }">{{ c.rate }}%</text>
    </view>
    <view class="sch-row" v-for="(yr, yi) in milestoneYears" :key="yr">
      <text class="sch-year">{{ yr }}</text>
      <text v-for="c in compareData" :key="c.rate" class="sch-num">{{ fmt(c.values[yi].value) }}</text>
    </view>
  </view>
</template>

<style>
.compare-bars { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.compare-bar-row { display: flex; align-items: center; gap: 8px; }
.compare-year { font-size: 11px; color: #71717a; width: 32px; text-align: right; flex-shrink: 0; }
.compare-bar-track { flex: 1; height: 10px; background: #1e1e22; border-radius: 5px; display: flex; overflow: hidden; }
.compare-bar-seg { height: 100%; min-width: 2px; }
</style>
```

关键点：
- 用一个 100% 宽度的 track，各数据段用 `width` 百分比渲染
- 下方配数值表展示精确数据
- 舍弃 touch 十字光标交互（小程序中无 SVG 难以实现精确的 touch→数据映射）

## 方案 C：Canvas（备选）

适合需要精确曲线或复杂交互的场景：
```ts
const ctx = uni.createCanvasContext('myChart')
ctx.setFillStyle('#09090b')
ctx.fillRect(0, 0, 340, 200)
// ... 绘制图表
ctx.draw()
```

缺点：代码量大、需要手动处理 devicePixelRatio、touch 坐标映射。
