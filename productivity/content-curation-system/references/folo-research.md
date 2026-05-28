# Folo 研究结论（2026-05-12 实测）

## 核心结论

**Folo 无法通过 API 获取数据**，是闭源 SaaS，数据存在 RSSNext 的服务器上。

官网：follow.is / folio.is
GitHub：github.com/RSSNext/Folo（38.3k stars）
技术栈：RSSHub 闭源商业版 + 住宅代理 IP 池 + Playwright 自动化

## 为什么 Folo 能抓 Twitter/B站/公众号

Folo 背后是 RSSNext 自建的基础设施：
- **住宅代理 IP 池**：绕过平台对数据中心 IP 的反爬
- **内置 Playwright**：浏览器渲染，B站等需要 JS 加载的内容才能抓
- **1543 个官方数据源**：每个平台有定制爬虫，专门维护
- **闭源商业方案**：这些资源个人用户无法自建

## Folo 的定价（2026-05-12）

| 方案 | 价格 | RSSHub 订阅数 | AI 摘要/天 |
|------|------|-------------|-----------|
| Free | $0 | 30 | 3 |
| Basic | $4.17/月 | 200 | 30 |
| Plus | $8.33/月 | 500 | Unlimited |
| Pro | $83.33/月 | 5000 | Unlimited |

RSSHub 订阅数包含 Twitter/B站/公众号等非标准 RSS 源，说明这些是靠 RSSHub 基础设施工作。

## 集成可能性

**没有公开 API**，Folo 的 integrations 是单向推送（推送到 Telegram、Slack 等），不是数据拉取。

如果用户在用 Folo，正确的接入方式是：
1. 让用户在 Folo 里配置 Telegram integration，直接转发内容给你
2. 或者放弃 Folo 方案，用我们已有的 xreach + RSSHub + FreshRSS 组合

## 备选方案

**justoneapi**（⭐148）：dashboard.justoneapi.com，商业 API，支持 Twitter/B站/公众号/微博/小红书/抖音等，按调用量收费。

**自建 RSSHub**：diygod/rsshub Docker 镜像，但 Twitter/B站等 route 需要 Playwright，容器内安装有 npm 依赖冲突问题。

## 其他发现

- Folo 官网：follow.is（不是 folio.is）
- Folo 支持「bring your own key」（Plus 以上），可以接自己的 AI 模型
- Folo 有 Web App：app.folo.is
- Folo 是「RSSNext」组织的产品，同一个组织维护 RSSHub
