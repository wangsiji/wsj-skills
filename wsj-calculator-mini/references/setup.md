---
name: wsj-miniprogram-setup
description: 富足人生小程序从零搭建——项目初始化/路径约定/SFC命名冲突/pages.json配置/TabBar架构/图标生成。
---

## 二、项目搭建（Setup）

从零开始搭建 UniApp + Vue3 项目，输出微信小程序。

### 项目初始化

#### 1. 创建项目目录

```bash
mkdir -p miniprogram/src/{pages/index,components,utils}
```

#### 2. package.json

```json
{
  "name": "xxx-mini",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev:mp-weixin": "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin"
  },
  "dependencies": {
    "@dcloudio/uni-app": "3.0.0-xxx",
    "vue": "^3.4.21",
    "pinia": "^2.1.7"
  },
  "devDependencies": {
    "@dcloudio/vite-plugin-uni": "3.0.0-xxx",
    "@dcloudio/types": "^3.4.8",
    "vite": "^5.2.8",
    "sass": "^1.77.0"
  }
}
```

#### 3. vite.config.ts

```ts
import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()]
})
```

#### 4. 核心文件

- `src/main.ts` — SSR App 入口
- `src/App.vue` — 根组件
- `src/pages.json` — 页面路由配置
- `src/manifest.json` — App/小程序配置（**AppID 在这里改**）
- `src/pages/index/index.vue` — 首页

#### 5. 安装依赖

```bash
npm install
```

#### 6. 构建

```bash
node_modules/.bin/uni build -p mp-weixin > /tmp/uni_build.log 2>&1
```

#### 7. 微信开发者工具导入

1. 下载微信开发者工具
2. 导入目录：`dist/build/mp-weixin`
3. AppID 在 `src/manifest.json` → `mp-weixin.appid`

### uni-app import 路径约定

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

当组件名与类型接口名相同时，用别名导入：

```ts
import ResultSummary from '../../components/ResultSummary.vue'
import type { ResultSummary as IResultSummary } from '../../utils/types'
```

### pages.json 必须配置项

- `pages` 数组的第一个元素必须是 tabBar 页面（如果有 tabBar）
- 单页面应用不要配置 `lazyCodeLoading: "requiredComponents"`（已知导致生产环境 `ref is not defined`）
- import 路径：注意层级正确

### 已有项目添加新页面

1. 创建 `src/pages/<page>/<page>.vue`
2. 在 `pages.json` 的 `pages[]` 中注册路由
3. 重新构建
4. 微信开发者工具中刷新

> ⚠️ pages.json 注册了路由但文件不存在，构建时不会报错，但运行时页面会 404。

### TabBar 架构变更（3→2 tab）

步骤：
1. **pages.json** — 修改 `tabBar.list`，去掉对应 entry
2. **pages 数组顺序** — `pages[]` 的**第一个元素必须是 tabBar 页面**，否则 tabBar 完全不显示
3. **子页面返回按钮** — 用自定义导航栏

> ⚠️ **致命陷阱**：`uni.navigateBack()` 在页面栈为空时静默失败。正确做法：
> ```ts
> function goBack() {
>   const pages = getCurrentPages()
>   if (pages.length > 1) uni.navigateBack()
>   else uni.switchTab({ url: '/pages/tools/tools' })
> }
> ```

### TabBar 图标生成

⚠️ **纯色占位符 PNG 会被微信编译器拒绝**：

```python
from PIL import Image, ImageDraw, ImageFont
def make_icon(emoji, color_rgb, active):
    img = Image.new('RGBA', (81, 81), (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)
    bg_color = (*color_rgb, 40) if active else (39, 39, 48, 255)
    draw.ellipse([14, 14, 67, 67], fill=bg_color)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
    text_color = (*color_rgb, 255) if active else (180, 180, 190, 255)
    draw.text((40, 40), emoji, font=font, anchor='mm', fill=text_color)
    return img
```

### 全局错误处理（utils/toast.ts）

```ts
export function toast(title: string, icon: 'success' | 'error' | 'none' = 'none') {
  uni.showToast({ title, icon, duration: 2000 })
}
export function handleError(err: any, context = '') {
  uni.getNetworkType({
    success: (res) => {
      if (res.networkType === 'none') toast('网络已断开', 'none')
      else toast(`${context}失败`, 'none')
    }
  })
}
export function safeGetStorage<T>(key: string, fallback: T): T {
  try { const raw = uni.getStorageSync(key); return raw ? JSON.parse(raw) : fallback }
  catch { return fallback }
}
```

### 依赖版本（2026-04 实测可用）

- uni-app: `3.0.0-4060620250520001`
- vue: `^3.4.21`
- pinia: `^2.1.7`
- vite: `^5.2.8`
- sass: `^1.77.0`

---

