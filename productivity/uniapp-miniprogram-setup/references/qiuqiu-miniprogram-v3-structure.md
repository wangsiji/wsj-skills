# 秋秋开心小程序 v6 项目结构（2026-05-14 更新）

## 源码位置
`/home/wangsiji/projects/wsj-miniprogram/`

## 源码结构（v6 — 2-tab 架构，16 个页面）
```
src/
├── pages.json              # 路由配置 + tabBar 定义（2个tab）
├── manifest.json           # AppID: wxb6514fa4040c41d8
├── App.vue                 # 全局样式（深色主题 #0a0a0f）+ 启动屏
├── main.ts
├── pages/
│   ├── timebox/
│   │   ├── timebox.vue     # 时间盒 V5 — 计时器 + 待办清单 + 白噪音 + 统计
│   │   ├── report.vue      # 每周专注报告（周导航 + 分类分布 + 每日详情）
│   │   ├── achievements.vue # 成就殿堂（12枚勋章，localStorage 驱动）
│   │   └── studyroom.vue   # 自习室（在线人数 + 实时时间轴 + 公约）
│   ├── tools/
│   │   ├── tools.vue       # 工具箱首页（4个卡片）
│   │   ├── investment.vue  # 复利计算器（5模式 + 堆叠柱状图 + 年度表）
│   │   ├── savings.vue     # 储蓄计划（目标→月存→年限预测 + 面积图）
│   │   └── flipclock.vue   # 翻页时钟（全屏极简大字 + 3秒自动隐藏导航）
│   ├── mine/
│   │   ├── mine.vue        # 内容专区（免费5篇 + 付费6篇 + 统计 + 会员入口）
│   │   ├── profile.vue     # 个人中心（微信登录 + 头像昵称 + 数据面板）
│   │   ├── membership.vue  # 会员订阅（月/季/年 3档 + 微信支付预留）
│   │   ├── privacy.vue     # 隐私政策（6个条款）
│   │   └── agreement.vue   # 用户协议（8个条款）
│   └── articles/
│       ├── articles.vue    # 文章列表（按 free/paid 过滤）
│       └── read.vue        # 文章阅读（付费遮罩，会员状态预留）
├── static/
│   └── tabbar/
│       ├── tools.png / tools-active.png
│       └── mine.png / mine-active.png
```

## tabBar 配置（pages.json — 2-tab）
```json
"tabBar": {
  "color": "#71717a",
  "selectedColor": "#6366f1",
  "backgroundColor": "#0e0e10",
  "borderStyle": "black",
  "list": [
    { "pagePath": "pages/tools/tools", "text": "工具箱",
      "iconPath": "static/tabbar/tools.png",
      "selectedIconPath": "static/tabbar/tools-active.png" },
    { "pagePath": "pages/mine/mine", "text": "内容专区",
      "iconPath": "static/tabbar/mine.png",
      "selectedIconPath": "static/tabbar/mine-active.png" }
  ]
}
```

## 页面导航闭环

```
工具箱首页 → 时间盒 → 报告 / 成就 / 自习室
    ↓          ↓          ↓
  储蓄计划   白噪音面板   统计数据
    ↓
  翻页时钟

内容专区 → 文章列表 → 文章阅读（付费遮罩）
    ↓         ↓
  个人中心   免费/付费过滤
    ↓
  会员订阅（3档套餐）

底部链接：隐私政策 / 用户协议 / 联系我们
```

| 起点 | 目标 | 方法 |
|------|------|------|
| tools 工具箱卡片 | timebox / investment / savings / flipclock | `uni.navigateTo` |
| mine 内容专区 | articles / read / profile / membership | `uni.navigateTo` |
| mine 用户卡片 | profile（个人中心） | `uni.navigateTo` |
| mine VIP 徽章 | membership（会员订阅） | `uni.navigateTo` |
| timebox 统计区 | report / achievements / studyroom | `uni.navigateTo` |
| 子页面返回 | 上级页面 | **自定义返回按钮** `goBack()` |

> ⚠️ 所有子页面使用统一的 `goBack()` 函数（含 `switchTab` fallback），禁止直接 `@click="uni.navigateBack()"`。

## 时间盒数据结构

### 专注记录（localStorage key: `timebox_v2_records`）
```ts
interface Record {
  id: string        // Date.now().toString()
  duration: number  // 分钟
  tag: string       // 'deep'|'study'|'parent'|'sport'|'create'|'rest'
  task: string      // 用户输入的任务名
  ts: number        // Date.now()
}
// 按日期分组: { '2025-05-13': Record[] }
```

### 待办清单（localStorage key: `timebox_todos`）
```ts
interface Todo {
  id: string
  title: string     // 任务名
  tag: string       // 标签 ID
  completed: boolean
  totalMins: number // 累计专注时长
  sessions: number  // 专注次数
  createdAt: number
}
```

### 成就系统（读取全量 records，12枚勋章本地计算）
- 次数勋章：1次 / 10次 / 100次
- 时长勋章：5h / 50h / 100h
- 连胜勋章：3天 / 7天 / 30天
- 分类勋章：深度工作10h / 运动5h / 学习10h

### 白噪音（uni.createInnerAudioContext，4种音景）
- 雨声 🌧 / 森林 🌲 / 海浪 🌊 / 咖啡馆 ☕
- 循环播放，音量可调，静默容错
- 非专注状态下显示，组件卸载时自动停止

## 会员订阅结构
```ts
// 3档套餐，预留微信支付接口
PLANS = [
  { id: 'monthly', price: 19.9, features: ['解锁付费文章','专属社群','深度长文'] },
  { id: 'quarterly', price: 49.9, features: [...monthly, '1v1答疑','模板','复盘报告'] },
  { id: 'yearly', price: 168, features: [...quarterly, '全年12次答疑','成长档案','共创'] },
]
// 支付预留：uni.login() → 后端换 openid → 统一下单 → uni.requestPayment()
```

## 标签定义
```ts
const TAGS = {
  deep:   { label: '深度工作', color: '#6366f1' },
  study:  { label: '学习',     color: '#3b82f6' },
  parent: { label: '带娃',     color: '#f59e0b' },
  sport:  { label: '运动',     color: '#22c55e' },
  create: { label: '创作',     color: '#ec4899' },
  rest:   { label: '休息',     color: '#71717a' }
}
```

## 每周报告统计逻辑
- 周范围：周一到周日（西方习惯）
- 连续天数：中断后重新计数
- 存储上限：只保留365天数据

## 文章数据
文章列表目前使用 demo 数据硬编码，接口预留标注：
- `GET /api/articles?type=free|paid` — 免费/付费文章列表
- `GET /api/stats` — 用户统计数据
- `POST /api/login` — 微信 code 换 token
- `POST /api/membership/verify` — 验证会员状态

未来替换方向：
1. 公众号草稿 Markdown 文件 → 小程序本地渲染
2. 云开发数据库 → 动态更新无需发版
3. REST API → 独立后端内容管理
