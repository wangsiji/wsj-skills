---
name: time-box-project
description: 时间盒项目 — 3篇文章+微信小程序配套交付，文章与小程序功能一一对应
category: productivity
version: 3.0.0
---

# 时间盒项目

## 项目结构（v3 — 2026-05-13 重组后）

```
/home/wangsiji/projects/
├── miniprogram/                    # UniApp 开发目录（≠ 旧 time-box/）
│   ├── dist/build/mp-weixin/      # 微信开发者工具导入此目录
│   ├── src/
│   │   ├── pages.json             # 3 TabBar + 2 普通页面
│   │   ├── App.vue
│   │   ├── manifest.json          # AppID: wxb6514fa4040c41d8
│   │   ├── static/tabbar/         # 6个 tabBar 图标 PNG
│   └── pages/
│       ├── timebox/
│       │   ├── timebox.vue    # Tab1: 计时器 ✅
│       │   └── report.vue     # 每周专注报告 ✅ v3.1
│       ├── tools/
│       │   ├── tools.vue      # Tab2: 工具箱列表 ✅
│       │   └── investment.vue # 复利计算器 ✅ v3.1
│       ├── mine/mine.vue      # Tab3: 我的数据 ✅
│       └── articles/          # 付费文章 ✅ v3
│   └── preview.html               # HTML 原型
│
└── wsj-second-brain/秋秋很开心/articles/  # 配套文章（≠ miniprogram/articles/）
    ├── 01-原理篇.md
    ├── 02-工具演示篇.md
    └── 03-补充篇.md
```

> ⚠️ 旧 `/home/wangsiji/projects/time-box/` 已删除。重组后的项目根目录是 `miniprogram/`（小程序代码）和 `wsj-second-brain/秋秋很开心/`（文章）。

## 小程序功能（v4 — 2-Tab 架构，2026-05-14）

| Tab | 路径 | 功能 |
|-----|------|------|
| 工具箱 | `pages/tools/tools` | 工具入口卡片（时间盒、复利计算器），可点击跳转 |
| 内容专区 | `pages/mine/mine` | 免费文章 + 付费文章列表，底部隐私政策链接 |

**子页面（非 Tab）**：
- `pages/timebox/timebox`：计时器 + 环形进度 + 今日统计 + 周柱状图
- `pages/tools/investment`：复利计算器（5模式 + 保存/加载方案 + SVG增长图）
- `pages/timebox/report`：每周专注报告（周导航 + 分类分布）
- `pages/articles/articles`：文章列表（免费/付费）
- `pages/articles/read`：文章阅读页（付费遮罩）
- `pages/mine/privacy`：隐私政策

**v4 新增功能（2026-05-14）**：
- **隐私政策页面**：合规必备，内容专区底部入口
- **时间盒空状态**：无记录时显示引导文案「选择一个计时器，开始你的第一次专注」
- **复利计算器保存方案**：保存/加载/删除（最多10条，存 Storage）
- **复利计算器利息高亮**：利息收益数字用绿色显示

**付费文章**（普通页面，非 Tab）：
| 路径 | 功能 |
|------|------|
| `pages/articles/articles` | 文章列表（封面/标签/付费标记） |
| `pages/articles/read` | 阅读页（付费遮罩，付费文强制显示遮罩） |

## 构建与部署

```bash
# 构建微信小程序
cd /home/wangsiji/projects/miniprogram
npm run build:mp-weixin
# 产物: dist/build/mp-weixin/ → 微信开发者工具导入

# HTML 原型部署
sudo cp /home/wangsiji/projects/miniprogram/preview.html /var/www/html/preview.html
# 访问: http://192.3.16.123/preview.html
```

## 开发原则

用户说过：**"不要一直问我，要开发第一版，然后我们再迭代"**。执行方式：

- 架构设计自己拿主意，不逐个细节确认
- 遇到不确定的地方做完后说明，不卡住
- 用户 review 后根据反馈迭代

## 主动迭代执行模型（持续迭代任务）

对于"持续迭代 X 小时"类任务：

- **报告节奏**：用 cron job 驱动定时汇报（每 30 分钟一次）
- **迭代执行**：`delegate_task` 立即启动，不需要等 cron 时间表
- **验证标准**：每次迭代后必须执行 `npm run build:mp-weixin` 确认构建成功
- **subagent 可靠性**：subagent 报告的改动需用构建结果验证，不能只看报告

```bash
# 立即启动迭代（不等 cron 时间表）
delegate_task → 选择功能 → 实现 → npm run build:mp-weixin → 汇报

# cron 只负责定时报告，不是迭代触发的条件
```

**已知坑**：subagent 有时报告"改动成功"但文件路径拼错（如 `w*ings*iji` vs `w*angs*iji`）。每次用构建命令验证实际产物。

## 原型先行工作流

标准顺序：
1. 先做 HTML 原型（可运行的交互原型）
2. 部署到 nginx（`sudo cp ... /var/www/html/preview.html`）
3. 发链接给用户 Telegram 预览
4. 用户确认后再写 UniApp 代码

```python
# Telegram 发送
send_message(message="http://192.3.16.123/preview.html", target="telegram:wang siji")
send_message(message="MEDIA:/home/wangsiji/projects/miniprogram/preview.html", target="telegram:wang siji")
```

**Telegram chat_id**: `7128007362`

## Tab Bar 兼容性（重要坑）

uni-app + HTML 原型开发中，Tab Bar 图标**不要用 emoji**：

| 图标类型 | 示例 | 问题 |
|----------|------|------|
| Emoji | ◉ ✡ ◎ ⬡ ○ | iOS Safari/WeChat 渲染为黑色，完全不可见 |
| Unicode几何符号 | ● ✦ ◯ | 部分安卓机也渲染异常 |
| 中文首字 | 时 工 圈 | ✅ 全平台可靠渲染 |

**正确方案**：Tab 图标用中文首字或 PNG 图片
```html
<!-- ✅ 正确：中文首字 + 样式 -->
<span class="tab-icon" style="font-size:15px;color:#6366f1;font-weight:900">时</span>

<!-- ❌ 错误：emoji 在移动浏览器渲染为黑色 -->
<span class="tab-icon">◉</span>
```

**v4 Tab Bar 配置**（2个Tab，必须满足）：
```json
"tabBar": {
  "list": [
    { "pagePath": "pages/tools/tools", "text": "工具箱" },
    { "pagePath": "pages/mine/mine", "text": "内容专区" }
  ]
}
```

**关键规则**：`pages.json` 中 `pages[0]` 必须是 tabBar 页面，否则小程序加载失败。当前 `pages[0] = pages/tools/tools`。

## uni-app 已知 Bug 与修复

| 问题 | 症状 | 修复 |
|------|------|------|
| **subPackages undefined** | 框架报错 `subPackages is not defined` | pages.json 添加 `"subPackages": []` 空数组 |
| **动态 handler 编译异常** | `@click="open(obj)"` 编译成 `bindtap="{{obj.k}}"` 微信 WXML 不支持 | 改为 `@click="open(obj.id)"`，handler 用 `Record<id,path>` 查表 |
| **pages[0] 非 TabBar** | 小程序彻底打不开 | 确保 pages 数组第一个是 tabBar 页面 |

详细 Bug 列表：见 `references/uniapp-known-bugs.md`

## 文章与工具对应关系

- **01-原理篇**：教育内容，工具入口改为「秋秋很开心小程序 → 底部 Tab 时间盒」
- **02-工具演示篇**：3步上手 + FAQ + 底部7天柱状图，已更新小程序截图描述
- **03-补充篇**：工具地址同上

## uni-app 构建静态资源规则

**根目录 `static/` 被 uni-app 构建系统忽略**。所有静态资源（tabbar 图标、图片等）必须放在 `src/static/` 下才会被复制到构建产物。

```
❌ 错误: /home/wangsiji/projects/miniprogram/static/tabbar/    → 不被复制
✅ 正确: /home/wangsiji/projects/miniprogram/src/static/tabbar/ → 复制到 dist/build/mp-weixin/static/tabbar/
```

每次添加新图标后记得确认构建产物里有：
```bash
find /home/wangsiji/projects/miniprogram/dist/build/mp-weixin/static/ -name "*.png"
```

## AppID 与关键路径

- **AppID**: `wxb6514fa4040c41d8`
- **VPS IP**: `192.3.16.123`
- **nginx 静态目录**: `/var/www/html/`（需要 sudo）
- **storage key**: `timebox_proto_v2`（原型）/ `timebox_v2_records`（小程序）
- **Record 结构**: `{ id, duration, tag, task, ts }`

## 产品战略（默会知识框架）

**核心定位**：「默会知识实践公司」，不是内容/工具公司。
**产品矩阵**：工具 → 数据 → 社群 → 内容

**变现路径**：
1. 工具免费引流（时间盒）
2. 每周专注报告（时间盒核心产出）
3. 老婆付费文章（已有100万粉渠道）
4. FIRE实践圈（远期）

**关键约束**：所有输出必须通过老婆 IP，无法独立身份出声。
