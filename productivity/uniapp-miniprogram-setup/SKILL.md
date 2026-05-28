---
name: uniapp-miniprogram-setup
description: UniApp 开发微信小程序项目搭建
triggers:
  - "搭建小程序"
  - "创建 uni-app 项目"
  - "小程序项目结构"
  - "项目有什么页面"
  - "miniprogram setup"
---

# UniApp 开发微信小程序项目搭建

## 适用场景
从零开始搭建 UniApp + Vue3 项目，输出微信小程序。

## 项目初始化步骤

### 1. 创建项目目录
```bash
mkdir -p miniprogram/src/{pages/index,components,utils}
```

### 2. package.json
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

### 3. vite.config.ts
```ts
import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()]
})
```

### 4. 核心文件
- `src/main.ts` — SSR App 入口
- `src/App.vue` — 根组件
- `src/pages.json` — 页面路由配置
- `src/manifest.json` — App/小程序配置（**AppID 在这里改**）
- `src/pages/index/index.vue` — 首页

### 5. 安装依赖
```bash
npm install
# 可能有很多 deprecated 警告，不用管
```

### 6. 构建微信小程序
⚠️ **关键**：`npm run dev:mp-weixin` 会尝试在前台运行导致超时，必须用 background 模式：

```bash
# 构建（后台运行）
node_modules/.bin/uni build -p mp-weixin > /tmp/uni_build.log 2>&1
cat /tmp/uni_build.log
```

### 7. 微信开发者工具导入
1. 下载微信开发者工具：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
2. 导入目录：`dist/build/mp-weixin`
3. AppID 在 `src/manifest.json` → `mp-weixin.appid` 替换

## 已有项目添加新页面

在已有项目中新增页面：
1. 创建 `src/pages/<page>/<page>.vue`
2. 在 `pages.json` 的 `pages[]` 中注册路由
3. 重新 `uni build -p mp-weixin`
4. 微信开发者工具中刷新

> ⚠️ pages.json 注册了路由但文件不存在，构建时不会报错，但运行时页面会404。

### TabBar 架构变更（3→2 tab）

当需要把 3-tab 改成 2-tab 时（如去掉时间盒 tab），步骤：

1. **pages.json** — 修改 `tabBar.list`，去掉对应 entry，`text` 改为新名称
2. **pages 数组顺序** — `pages[]` 的**第一个元素必须是 tabBar 页面**。删除 tabBar 条目后，必须把剩余 tabBar 页面排到数组第一位，否则 tabBar 完全不显示（微信开发者工具里看不到任何 tab）。
3. **工具箱页面**（如 `tools.vue`）— 工具卡片可直接 `uni.navigateTo` 到子页面
4. **子页面返回按钮** — 用自定义导航栏而非依赖 `uni.navigateBack()`

> ⚠️ **致命陷阱 - pages 数组第一个必须是 tabBar 页面**：
> 删除一个 tabBar 页面后，如果 `pages[0]` 变成非 tabBar 页面（如 `timebox`），小程序会完全无法加载——微信开发者工具里看不到任何 tabBar，首页也打不开。
> **修复**：把剩余的 tabBar 页面（如 `tools`）手动移到 `pages[]` 数组的第一位。
>
> ⚠️ **关键陷阱 - `uni.navigateBack()` 静默失败**：
> `uni.navigateBack()` 在页面栈为空时调用会静默失败（无任何提示）。**正确做法**：给所有子页面加自定义返回按钮 + 兜底逻辑。
>
> ```ts
> function goBack() {
>   const pages = getCurrentPages()
>   if (pages.length > 1) {
>     uni.navigateBack()
>   } else {
>     uni.switchTab({ url: '/pages/tools/tools' }) // 必须是 tabBar 页面
>   }
> }
> ```
>
> ⚠️ **Vue 文件补丁必须整文件重写**：对 `.vue` 文件做结构性修改（插入新函数、computed、修改 script 逻辑）时，`patch` 操作可能导致 Vue SFC 结构破坏——旧函数体残留在新代码后面，形成孤立片段。一旦发现 patch 后文件出现语法残留或计算属性断裂，**立即放弃 patch，改用 `write_file` 重写整个文件**。典型信号：构建报错、孤立语句、代码块未闭合。
>
> **正确工作流**：结构性改动 → 直接 `write_file` 完整文件。小的纯文本替换（如文案、样式）才用 patch。

### TabBar 图标生成

⚠️ **纯色占位符 PNG 会被微信编译器拒绝**。必须使用有实际图形内容的图标，推荐用 PIL 渲染 emoji：

```python
# 依赖：PIL (pip install Pillow)
from PIL import Image, ImageDraw, ImageFont

def make_icon(emoji, color_rgb, active):
    img = Image.new('RGBA', (81, 81), (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)
    bg_color = (*color_rgb, 40) if active else (39, 39, 48, 255)
    draw.ellipse([14, 14, 67, 67], fill=bg_color)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
    except:
        font = ImageFont.load_default()
    text_color = (*color_rgb, 255) if active else (180, 180, 190, 255)
    draw.text((40, 40), emoji, font=font, anchor='mm', fill=text_color)
    return img

icons = [('timebox', '\u23f1', (99, 102, 241)), ('tools', '\ud83e\udd70', (99, 102, 241)), ('mine', '\ud83d\udc64', (99, 102, 241))]
for name, emoji, color in icons:
    make_icon(emoji, color, False).save(f'static/tabbar/{name}.png')
    make_icon(emoji, color, True).save(f'static/tabbar/{name}-active.png')
```

> ⚠️ 微信小程序要求 tabbar 图标有实际可见内容，不能是纯色块。尺寸 81x81。emoji 用 Unicode 转义。生产项目建议替换为设计师图标。

## pages.json 必须配置项

- `pages` 数组的第一个元素必须是 tabBar 页面（如果有 tabBar）
- 单页面应用不要配置 `lazyCodeLoading: "requiredComponents"`（已知导致生产环境 `ref is not defined`）
- 无分包时 `subPackages` 写空数组或省略均可（新版已不强制）

## 开发原则：先独立交付，再迭代

**核心原则**：开发第一版时不提问自己做决定，完成后用户 review 再迭代。不要一直问用户确认每个细节。

具体执行：
- 架构设计：自己拿主意（3-tab、多工具、付费文章栏目等）
- 功能细节：选最简单可靠的方案实现
- 样式/文案：按第一性原理推断用户偏好（简洁、高效、深色）
- 不确定的地方：做完后说明"这里可能需要调整"，让用户决定

> ⚠️ 这个原则是这个项目的默认工作方式。用户明确说过"不要一直问我，要开发第一版，然后我们再迭代"。

## 投资/复利计算器实现参考

### 高发 Bug（wsj-miniprogram 经验）
> 详细清单：[`references/wsj-miniprogram-bugs-20260514.md`](./references/wsj-miniprogram-bugs-20260514.md)
> 详细清单（2026-05-29）：[`references/wsj-miniprogram-bugs-20260529.md`](./references/wsj-miniprogram-bugs-20260529.md)

### v-html SVG touch 事件修复方案

微信小程序通过 `rich-text`（v-html）渲染 SVG 时，SVG 内部元素的 touch 事件无法冒泡到 Vue 组件层。正确做法：

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

### 项目清理检查清单

发现项目中存在冗余目录/文件时，清理步骤：
1. `du -sh <dir>` 确认大小（避免误删有用内容）
2. `grep -r "tabbar\|static" src/` 确认无引用后再删
3. 从 git 暂存区移除：`git reset HEAD dist/`
4. 重新构建验证：`npm run build:mp-weixin`
5. 提交变更

### 快速判断项目是否重复

```
# 如果存在以下特征，说明项目有冗余复制：
- 根目录有 src/，同时根目录下有 miniprogram/src/
- 根目录有 node_modules，同时 miniprogram/ 下也有独立 node_modules/
- static/tabbar/ 下有图标但 src/ 中无任何 tabbar 配置引用
```

### 5种计算模式

| Tab | 已知 | 求 | 公式要点 |
|-----|------|-----|---------|
| 终值 | 本金/利率/定投/年限 | 最终金额 | `calcFV()` |
| 定投 | 终值/利率/年限 | 每月投多少 | `calcPMT()` |
| 收益率 | 本金/终值/定投/年限 | 年化多少 | `calcRate()` Newton法 |
| 本金 | 终值/利率/定投/年限 | 初始要多少 | `calcPV()` |
| 年限 | 本金/终值/利率/定投 | 要投多久 | `calcYears()` 二分法 |

> ⚠️ **EAR（有效年利率）是金融计算器行业标准**。每期利率 = `(1 + r/100)^(1/compound) - 1`，**不是** `r/100/compound`。详细公式见 `uniapp-miniprogram-optimization` skill。

### 复利频率选项（月/季/半年/年/周/日/连续）
```ts
const compoundMap = { 1:'每年', 2:'半年', 4:'每季度', 12:'每月', 26:'每双周', 52:'每周', 365:'每日', 0:'连续' }
// n=0 时用连续复利: A = P × e^(rt)
```

### SVG面积图（v-html渲染）
⚠️ **SVG `<line>` 元素禁止重复属性**：Vue 模板中用 `v-for` 渲染多条 line 时，两个端点坐标必须分别用 `:y1` + `:y2`，不能给同一元素绑定两次 `:y1`。构建时报 `[vite:vue] Duplicate attribute` 且行号指向 SVG line 元素时，首先检查是否有两个相同的坐标绑定。
```ts
// 错误 ❌ — Duplicate attribute y1
<line :x1="padX" :y1="..." :x2="W" :y1="..." ... />

// 正确 ✓
<line :x1="padX" :y1="..." :x2="W" :y2="..." ... />
```
> 详细 bug 记录：[`references/wsj-miniprogram-bugs-20260527.md`](./references/wsj-miniprogram-bugs-20260527.md) — 2026-05-28 session 章节
```ts
const chartData = computed(() => {
  if (!schedule.value.length) return ''
  const W = 340, H = 140, PAD = 12
  const vals = schedule.value.map(r => r.balance)
  const max = Math.max(...vals)
  const xStep = (W - PAD * 2) / (vals.length - 1)
  const pts = vals.map((v, i) => {
    const x = PAD + i * xStep
    const y = PAD + (1 - v / max) * (H - PAD * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const areaPath = `M${PAD},${H-PAD} L${pts.join(' L')} L${W-PAD},${H-PAD} Z`
  return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">
    <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#6366f1" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#6366f1" stop-opacity="0.02"/>
    </linearGradient></defs>
    <path d="${areaPath}" fill="url(#g)"/>
    <path d="M${pts.join(' L')}" fill="none" stroke="#6366f1" stroke-width="2"/>
  </svg>`
})
```
> ⚠️ v-html 在 UniApp webview 环境中可用，纯原生小程序不支持。需图表时建议用 webview 或外部组件。

## 微信小程序 webview 接入文章

小程序内嵌入文章/网页有几种方式：

### 方式一：webview 组件（需已备案域名）
```vue
<template>
  <web-view :src="articleUrl" />
</template>
```
**要求**：域名必须在微信小程序管理后台添加 JS 安全域名（业务域名）。个人小程序通常只能用 `https://mp.weixin.qq.com/` 开头。

### 方式二：直接渲染 Markdown（推荐，无需域名备案）
将文章内容存在小程序本地或云数据库，用 `uParse` 或第三方 MarkDown 组件渲染。
优点：不依赖外部域名、不需备案。缺点：文章更新需要重新发版或配合云开发。

### 方式三：webview 打开公众号文章（最简方案）
公众号已群发文章可以直接用 webview 打开（微信内部会自动适配）：
```
web-view src="https://mp.weixin.qq.com/s/xxxxx"
```
**注意**：需要在小程序后台添加 `https://mp.weixin.qq.com` 到 JS 安全域名。

## 常见问题

### npm install peer dependency warnings
不用管，依赖装上了就行

### vite build 前台模式报错
必须用后台模式，不能直接前台运行：
```bash
node_modules/.bin/uni build -p mp-weixin > /tmp/uni_build.log 2>&1 &
```
查看日志：`tail -f /tmp/uni_build.log`

### 编译报 "Unexpected token" 但代码看起来没问题
通常是 Vue 模板里有多余的 `}` 或语法错误，错误指向的行号不准确。从可疑的函数（如 `sendNotify`）开始逐段注释排查。

### 小程序不显示内容
检查 `src/pages.json` 的 `globalStyle.navigationStyle` 是否设为 `custom`，如果是需要手动隐藏原生导航栏：
```ts
uni.hideHomeButton({})
```

## 相关参考

- [秋秋开心小程序 v4 项目结构（16页）](./references/qiuqiu-miniprogram-v4-structure.md) — 当前最新
- [秋秋开心小程序 v3 项目结构](./references/qiuqiu-miniprogram-v3-structure.md) — 历史版本
- [原型部署与 Telegram 分享](./references/prototype-deploy-telegram.md)
- [uniapp 动态 handler bug + pages[0] 致命问题](./references/uniapp-dynamic-handler-bug.md)
- [wsj-miniprogram 高发 Bug 清单 (2026-05-14)](./references/wsj-miniprogram-bugs-20260514.md)
- [wsj-miniprogram 高发 Bug 清单 (2026-05-27)](./references/wsj-miniprogram-bugs-20260527.md)
- [wsj-miniprogram 高发 Bug 清单 (2026-05-29)](./references/wsj-miniprogram-bugs-20260529.md)
- [wsj-miniprogram Git Workflow](./references/git-workflow-wsj-miniprogram.md)
- [原型自检脚本](../scripts/verify-preview.py) — 截图 + 像素分析

## 全局错误处理（utils/toast.ts）

新建项目时建议加入此工具模块：

```ts
// src/utils/toast.ts
export function toast(title: string, icon: 'success' | 'error' | 'none' = 'none') {
  uni.showToast({ title, icon, duration: 2000 })
}

export function handleError(err: any, context = '') {
  uni.getNetworkType({
    success: (res) => {
      if (res.networkType === 'none') toast('网络已断开，请检查连接', 'none')
      else toast(context ? `${context}失败` : '网络错误，请重试', 'none')
    }
  })
}

export function safeGetStorage<T>(key: string, fallback: T): T {
  try { const raw = uni.getStorageSync(key); return raw ? JSON.parse(raw) : fallback }
  catch { return fallback }
}
```

用途：所有 `uni.request` 调用统一 `catch` → `handleError`；所有 `JSON.parse(uni.getStorageSync(...))` 改为 `safeGetStorage`。

## 自检流程：发给用户前必须验证

**核心原则**：发给用户的东西，自己先100%确认没问题。不要说"试试看"、"应该好了"。

### 验证方法一：DOM + CSS 直接确认（必须做）

发预览链接前，用 curl 直接验证 HTML 内容正确：

```bash
# 1. 验证 Tab Bar HTML 结构完整
curl -s http://192.3.16.123/preview.html | python3 -c "
import sys, re
html = sys.stdin.read()
tb = re.search(r'<div class=\"tab-bar\">(.*?)</div>\s*</div>', html, re.DOTALL)
if tb:
    labels = re.findall(r'class=\"tab-label\"[^>]*>([^<]+)</span>', tb.group(1))
    print('Tab labels:', labels)
    print('Tab bar HTML 完整 ✓' if len(labels) == 3 else 'Tab bar 结构不完整 ✗')
else:
    print('ERROR: 未找到 tab-bar HTML')
"

# 2. 验证 CSS 关键样式
curl -s http://192.3.16.123/preview.html | python3 -c "
import sys, re
html = sys.stdin.read()
css = re.findall(r'\.tab-bar\s *{([^}]+)}', html)
if css:
    print('Tab bar CSS:', css[0].replace('  ', '\n'))
"
```

**必须检查的内容**：
- Tab Bar 存在且有3个 tab-item
- 每个 tab-label 文字正确（秋秋很开心/工具箱/圈圈）
- 背景色是浅色（#ffffff 或 #f0f0f5），不是透明
- 文字颜色是深色（#333 或 #444）

### 验证方法二：Headless 截图（辅助参考）

⚠️ **已知局限**：Headless Chromium 对 `position:fixed` 底部元素渲染不可靠——可能显示全白像素而实际浏览器正常显示。截图只能作为辅助，DOM 验证才是主要依据。

```bash
python3 ~/.hermes/skills/productivity/uniapp-miniprogram-setup/scripts/verify-preview.py
```

如果 DOM 验证通过但截图失败，仍可发送，但需注明「服务端截图工具可能有局限，以实际浏览器为准」。

### 验证方法三：发送前截图并发给用户确认

通过 Telegram 发送截图前，先自己用 vision 分析确认内容正确，不要只靠亮度数值：

```bash
# 截图后先检查关键区域是否有暗色像素（文字）
python3 -c "
from PIL import Image
import numpy as np
img = Image.open('/tmp/shot.png')
w, h = img.size
arr = np.array(img)
# Tab bar 区域（底部80px）应该有非白色像素（文字）
tab = arr[h-80:]
dark = (tab < 200).sum()
total = tab.size // 3
print(f'Tab bar 暗色像素: {dark}/{total} ({dark*100/total:.1f}%)')
# 如果 < 0.1% 说明没有渲染文字内容，需要排查
"
```

**发给用户的判断标准**：
- DOM 验证通过 → 可以在 Telegram 发截图 + 链接
- DOM 验证通过 + 截图显示内容 → 可以发链接让用户自己刷新测试
- DOM 验证失败 → 修复后再验证，不要发送

## 依赖版本（2026-04 实测可用）
- uni-app: `3.0.0-4060620250520001`
- vue: `^3.4.21`
- pinia: `^2.1.7`
- vite: `^5.2.8`
- sass: `^1.77.0`
