# uniapp-miniprogram-setup 2026-05-14 session notes

## 致命 Bug：tabBar 页面必须位于 pages[0]

**问题**：在微信开发者工具里，小程序完全打不开，tabBar 不显示，没有任何错误提示。

**原因**：把时间盒从 tabBar 删除后，`pages.json` 的 `pages[]` 数组里 timebox 还在第一位（它是普通子页面了），导致第一个加载的页面不是 tabBar 页面。

**症状**：
- 微信开发者工具里看不到任何 tabBar
- 首页空白
- 控制台无错误

**修复**：
```json
{
  "pages": [
    { "path": "pages/tools/tools", ... },  // tabBar 页面必须排第一
    { "path": "pages/mine/mine", ... },
    { "path": "pages/timebox/timebox", ... },  // 非 tabBar 子页面放后面
    ...
  ]
}
```

**教训**：修改 tabBar 配置后，始终确保 `pages[0]` 是 tabBar 页面。

---

## uni-app Vue3 动态 Handler 绑定问题

**现象**：某些 `@click` 绑定的函数在编译成微信小程序后变成动态引用 `bindtap="{{...}}"` 而非静态 `bindtap="handlerName"`。

**原因**：uni-app 在 Vue3 + 小程序模式下，对模板中传入非原始类型（如整个对象）的 event handler 可能会生成动态引用。微信 WXML 对动态 handler 的支持不稳定。

**受影响场景**：
- `@click="open(tool)"` — 传入整个对象
- `@click="openArticle(article)"` — 传入整个对象
- `@click="selectTimer(t)"` — 传入整个数组元素对象（TIMERS 数组场景）

**解决**：始终传 ID（字符串/数字），handler 里用查找表：

```ts
// 错误：传对象
@click="open(tool)"
function open(tool: typeof tools[0]) { uni.navigateTo({ url: tool.path }) }

// 正确：传 id，handler 用查找表
@click="open(tool.id)"
function open(id: string) {
  const paths: Record<string, string> = {
    timebox: '/pages/timebox/timebox',
    investment: '/pages/tools/investment',
  }
  const path = paths[id]
  if (path) uni.navigateTo({ url: path })
}

// TIMERS 数组场景：传 index
@click="selectTimer(index)"
function selectTimer(index: number) {
  const timer = TIMERS[index]
  selectedTimer.value = timer
  remaining.value = timer.value * 60
}
```

验证编译产物中的 handler：
```bash
grep -o 'bindtap="[^"]*"' dist/build/mp-weixin/pages/tools/tools.wxml
# 正确：bindtap="e" (静态引用)
# 可能有问题：bindtap="{{tool.k}}" (动态引用)
```
