# uni-app 已知 Bug 与修复

## pages.json 必须规则

1. **`pages[0]` 必须是 tabBar 页面**。如果不是，小程序在部分设备上彻底打不开（白屏）。
2. **必须加 `"subPackages": []`**。uni-app 版本 `3.0.0-4060620250520001` 在无分包时框架报错。

```json
{
  "pages": [
    { "path": "pages/tools/tools", ... },  // tabBar page = pages[0]
    { "path": "pages/mine/mine", ... }
  ],
  "subPackages": [],
  "lazyCodeLoading": "requiredComponents"
}
```

## 动态 Handler 问题

微信 WXML 的事件绑定不支持动态表达式。uni-app 编译 `@click="open(tool)"`（传对象）会产生 `bindtap="{{tool.k}}"` 这样的动态引用，微信运行时会失效。

**正确写法**：传 `id`（基础类型），handler 里用 Record 查表。

```typescript
// ❌ 错：传对象，编译后产生动态 handler
@click="open(tool)"

// ✅ 对：传 id，handler 用 id 查找路径
@click="open(tool.id)"
// open(id: string) { const p = TOOL_MAP[id as keyof typeof TOOL_MAP]; uni.navigateTo({ url: p }) }
```

## 微信开发者工具调试

每次修复 bug 后，**必须清空后重新导入** `dist/build/mp-weixin/`，否则旧缓存导致仍然报错。

## SVG line 元素重复属性编译报错

uni-app + Vite 编译 Vue 单文件时，SVG `<line>` 元素不能用 `:y1` 绑定两次（v-for 内重复绑定同一属性会报 `Duplicate attribute`）。

**错误写法**：
```vue
<line
  v-for="pct in [0.25, 0.5, 0.75]"
  :key="pct"
  :x1="padX" :y1="(...)"
  :x2="W - padX" :y1="(...)"   <!-- ❌ y1 重复！应该是 y2 -->
  stroke="#27272a" stroke-width="1"
/>
```

**正确写法**：
```vue
<line
  v-for="pct in [0.25, 0.5, 0.75]"
  :key="pct"
  :x1="padX"
  :y1="(plotTop + pct * plotH).toFixed(1)"
  :x2="chartW - padX"
  :y2="(plotTop + pct * plotH).toFixed(1)"
  stroke="#27272a"
  stroke-width="1"
/>
```

注意：所有 SVG 动态属性都应用 `.toFixed(1)` 转为字符串，`v-for` 内 SVG 元素特别容易触发 Vue 模板编译器的属性去重逻辑。

## 子页面返回按钮

所有非 tabBar 子页面必须加自定义返回按钮（用户明确要求）：
```vue
<view class="back-btn" @click="uni.navigateBack()">‹</view>
```
微信原生导航栏的返回按钮用户无法自定义，且行为在不同场景下不一致。