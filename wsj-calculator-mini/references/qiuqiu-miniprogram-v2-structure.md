# 秋秋很开心小程序 v2 项目结构

> 更新时间：2026-05-13（项目目录重组后）

## 最终架构

```
/home/wangsiji/projects/
├── miniprogram/                    # UniApp 开发目录
│   ├── dist/build/mp-weixin/       # 微信开发者工具导入此目录
│   ├── src/
│   │   ├── pages.json             # 3个tab + 2个普通页面
│   │   ├── App.vue
│   │   ├── manifest.json          # AppID: wxb6514fa4040c41d8
│   │   ├── static/tabbar/         # tabBar 图标（6个 PNG）
│   │   └── pages/
│   │       ├── timebox/timebox.vue    # Tab1: 计时器
│   │       ├── tools/tools.vue        # Tab2: 工具箱列表
│   │       ├── mine/mine.vue          # Tab3: 我的数据 + 文章入口
│   │       └── articles/
│   │           ├── articles.vue        # 文章列表
│   │           └── read.vue           # 文章阅读页（付费遮罩）
│   └── preview.html                # HTML原型（手机浏览器打开）
│
└── wsj-second-brain/秋秋很开心/articles/  # 配套文章
    ├── 01-原理篇.md
    ├── 02-工具演示篇.md
    └── 03-补充篇.md
```

## 构建命令

```bash
cd /home/wangsiji/projects/miniprogram
npm run build:mp-weixin
# 产物: dist/build/mp-weixin/ → 微信开发者工具导入
```

## tabBar 配置（pages.json）

```json
{
  "tabBar": {
    "list": [
      { "pagePath": "pages/timebox/timebox", "text": "时间盒" },
      { "pagePath": "pages/tools/tools", "text": "工具箱" },
      { "pagePath": "pages/mine/mine", "text": "我的" }
    ]
  }
}
```

## TabBar 图标规格

- 尺寸：81×81 像素
- 格式：PNG（不可用 SVG）
- 命名：`{name}.png` / `{name}-active.png`
- 普通态：灰色
- 选中态：主题紫 #6366f1
- **不能用纯色占位符，必须有实际图形内容**（emoji 渲染可用 PIL）

## 多工具扩展

在 `tools/tools.vue` 的 `tools` 数组中追加：

```ts
{
  id: 'toolid',
  name: '工具名',
  desc: '简短描述',
  icon: '🔧',
  color: '#hexcolor',
  coming: true,   // true = 待上线，不可跳转
},
```

扩展步骤：
1. 创建 `src/pages/toolid/toolid.vue`
2. 在 `pages.json` 注册（tabBar 页面放 `tabBar.list`；普通页面放 `pages[]`）
3. 如果是 tabBar 页面，工具箱里 `tool-card` 去掉 `disabled` class
4. `npm run build:mp-weixin`

## 关键设计决策

- **storage key**: `timebox_proto_v2`（原型用）/ `timebox_v2_records`（小程序用）
- **数据存储**: localStorage，结构 `{ 'YYYY-MM-DD': Record[] }`
- **Record 结构**: `{ id, duration, tag, task, ts }`
- **付费遮罩**: 纯前端展示，无真实权限校验（待接入微信支付）
- **时间盒计时器**: 本地运行，关闭小程序计时暂停（无后台保活）

## HTML 原型部署

```bash
# 更新 nginx served 文件
sudo cp /home/wangsiji/projects/miniprogram/preview.html /var/www/html/preview.html

# 访问（手机浏览器）
http://192.3.16.123/preview.html
```

原型路径变更记录：
- 旧：`/home/wangsiji/projects/time-box/preview.html`（已删除）
- 新：`/home/wangsiji/projects/miniprogram/preview.html`
