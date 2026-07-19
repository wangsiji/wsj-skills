# 秋秋开心小程序 v4 项目结构（16 页，2026-05 更新）

## 源码位置
`/home/wangsiji/projects/wsj-miniprogram/`

## 源码结构（v4 — 2-tab 架构 + 16 页）

```
src/
├── pages.json              # 路由配置 + tabBar 定义（2个tab）
├── manifest.json           # AppID: wxb6514fa4040c41d8
├── App.vue                 # 全局样式（深色主题 #0a0a0f）+ 启动屏
├── main.ts
├── utils/
│   └── toast.ts            # 全局错误处理 + toast + safeGetStorage
├── pages/
│   ├── tools/
│   │   ├── tools.vue       # 工具箱列表（4个卡片）
│   │   ├── investment.vue  # 复利计算器（5种模式+堆叠柱状图）
│   │   ├── savings.vue     # 储蓄计划计算器
│   │   └── flipclock.vue   # 翻页时钟（全屏极简）
│   ├── timebox/
│   │   ├── timebox.vue     # 时间盒计时器 + 待办清单 + 白噪音
│   │   ├── report.vue      # 每周专注报告（周切换+分类分布）
│   │   ├── achievements.vue # 成就殿堂（12枚勋章自动计算）
│   │   └── studyroom.vue   # 自习室（在线+时间轴）
│   ├── mine/
│   │   ├── mine.vue        # 内容专区（5免费+6付费文章）
│   │   ├── profile.vue     # 个人中心（微信登录+数据面板）
│   │   ├── membership.vue  # 会员订阅（3档套餐+支付预留）
│   │   ├── privacy.vue     # 隐私政策
│   │   └── agreement.vue   # 用户协议
│   └── articles/
│       ├── articles.vue    # 文章列表（免费/付费分类）
│       └── read.vue        # 文章阅读（付费遮罩）
├── static/
│   └── tabbar/
│       ├── tools.png / tools-active.png
│       └── mine.png / mine-active.png
```

## tabBar 配置

```json
"tabBar": {
  "color": "#71717a",
  "selectedColor": "#6366f1",
  "backgroundColor": "#0e0e10",
  "borderStyle": "black",
  "list": [
    { "pagePath": "pages/tools/tools", "text": "工具箱" },
    { "pagePath": "pages/mine/mine", "text": "内容专区" }
  ]
}
```

## 页面导航图

```
工具箱首页 (tab)       内容专区 (tab)
├─ 时间盒              ├─ 个人中心
│  ├─ 每周报告         │  └─ 会员订阅
│  ├─ 成就殿堂         ├─ 文章列表
│  ├─ 自习室           │  └─ 文章阅读
│  └─ [白噪音面板]     ├─ 隐私政策
├─ 复利计算器          ├─ 用户协议
├─ 储蓄计划            └─ [联系我们弹窗]
└─ 翻页时钟
```

## 关键设计决策

- **deepseek-v4-pro** 模型用于代码生成
- 所有子页面有 `goBack()` fallback（`switchTab` 到对应 tab）
- 导航栏统一：`height:44px` + `border-bottom` + 32×32 返回按钮
- 付费标签统一金色 `#fef3c7 / #92400e`
- 会员订阅/支付/云同步均预留后端接口，标注 `POST /api/xxx`
- 自习室为演示模式，标注 `💡 演示模式`
