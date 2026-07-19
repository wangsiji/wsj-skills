# wsj-miniprogram Bug Patterns (2026-05-29 session)

## 新增 Bug 模式

| Bug | 原因 | 修复 |
|-----|------|------|
| v-html 渲染的 SVG touch 事件不生效 | 微信小程序 rich-text 组件不支持 SVG 内部事件冒泡 | touch 绑定在外层 wrapper view，用 `e.currentTarget.getBoundingClientRect()` 计算点击位置 |
| 项目中存在重复 miniprogram/ 子目录（231MB，17848个文件） | 之前在 miniprogram/ 下又装了一套独立项目 | 删除整个 miniprogram/ 目录，只保留根目录项目 |
| static/tabbar/ 等无引用静态资源 | 早期架构遗留，tabBar 删除后未清理 | 删除 static/（空目录）、push.sh、preview.html |
| dist/ 目录被 git 追踪 | .gitignore 未正确配置 | 从 git 暂存区移除：`git reset HEAD dist/` |
| ref<any> 无类型约束 | 历史代码遗留 | 替换为具体 TypeScript 接口（CalcResult 等） |
| fmt/fmtInt 函数重复定义在组件内 | 未抽离到 utils | 抽离到 src/utils/format.ts |
| 图表尺寸 magic number（W=340, H=200 等） | 硬编码在 computed 中 | 抽离为 CHART_W, CHART_H, PAD_* 等命名常量 |

## v-html SVG touch 事件修复

微信小程序通过 `rich-text`（v-html）渲染 SVG 时，SVG 内部元素的 touch 事件无法冒泡到 Vue 组件层。

```vue
<!-- 错误：touch 绑定在 SVG 标签上，不生效 -->
<template>
  <view v-html="chartSvg" @touchstart="onTouch" />
</template>

<!-- 正确：touch 绑定在外层 wrapper view 上 -->
<template>
  <view class="chart-wrapper" @touchstart="onCompareTouch">
    <rich-text :nodes="compareSvg" />
  </view>
</template>

<script setup>
function onCompareTouch(e: TouchEvent) {
  const wrapEl = e.currentTarget as HTMLElement
  if (!wrapEl) return
  const rect = wrapEl.getBoundingClientRect()
  const relX = e.touches[0].clientX - rect.left
  const relY = e.touches[0].clientY - rect.top
  // 用相对坐标判断点击位置
}
</script>
```

## 项目清理检查清单

1. `du -sh <dir>` 确认大小（避免误删有用内容）
2. `grep -r "tabbar\|static" src/` 确认无引用后再删
3. 从 git 暂存区移除：`git reset HEAD dist/`
4. 重新构建验证：`npm run build:mp-weixin`
5. 提交变更

## 快速判断项目是否重复

```
# 以下特征说明项目有冗余复制：
- 根目录有 src/，同时根目录下有 miniprogram/src/
- 根目录有 node_modules，同时 miniprogram/ 下也有独立 node_modules/
- static/tabbar/ 下有图标但 src/ 中无任何 tabbar 配置引用
```

## 本次清理结果

```
删除: miniprogram/ (231MB, 17848 files)
删除: screenshots/
删除: static/ (空目录)
删除: push.sh, preview.html
commit: 2884f8b4 — "chore: 清理冗余目录，精简项目结构"
```

清理后项目结构（精简至必要文件）：
```
wsj-miniprogram/
├── src/
│   ├── App.vue / main.ts / manifest.json / pages.json
│   ├── pages/index/index.vue   # 唯一页面
│   └── utils/
│       ├── format.ts          # fmt/fmtInt + 图表常量
│       └── types.ts           # TypeScript 接口
├── node_modules/
├── dist/                      # 构建产物
├── .gitignore / package.json / vite.config.ts
```