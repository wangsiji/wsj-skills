---
name: content-curation-system
description: 跨平台内容精选系统 — Twitter/公众号/RSS → 规则过滤 → LLM 评分 → Telegram digest
---

# Content Curation System — 信息精选系统

## Problem
跨平台（Twitter、公众号、B站、播客）内容过载，需要从噪声中识别真正有价值的内容。

> 📂 `references/freshrss-api-debugging.md` — FreshRSS Google Reader API 完整调试笔记
> 📂 `references/platform-rss-sources.md` — 各平台 RSS/内容源实测结果
> 📂 `references/folo-research.md` — Folo 无法获取数据的结论 + 原因

## Architecture — v3: 推荐系统 (2026-05-20)

信息输入系统已升级为 **推荐引擎架构**，项目路径：`~/projects/info-feed/`

```
~/projects/info-feed/
├── config.yaml              ← 统一配置：关注列表、作者权重、时间窗口
├── feed.py                  ← 主入口：recall → rank → output
├── recall/                  ← 多路召回层
│   ├── base.py              ← BaseRecall 基类 + Item 数据格式
│   ├── twitter.py           ← xreach 包装器
│   ├── bilibili.py          ← RSSHub 桥接（需自建 RSSHub）
│   ├── jike.py              ← 即刻 API（需配用户 UID）
│   └── xiaoyuzhou.py        ← RSS feed 解析
└── ranking/
    └── engine.py            ← 排序引擎
```

**推荐系统工作流**：

```
【阶段一】多路召回 → 【阶段二】排序 → 【阶段三】输出
```

### 排序引擎

打分公式：
```
score = 作者权重 × 内容类型权重 × 时效性衰减 + 互动热度加分
```

- **作者权重**: 可自定义 (1-10)，如 karpathy=10, sama=9
- **内容类型权重**: longform=1.3, video=1.1, podcast=1.2, short=1.0, repost=0.7
- **时效性衰减**: 半衰期 8 小时 (每过 8h 分数减半)
- **互动加分**: log₂(1 + likes+retweets+replies) × 0.1

### 配置驱动 (config.yaml)

所有可配置项集中在 `config.yaml`，不再需要改代码即可增减关注列表和调整权重：

```yaml
recall:
  twitter:
    enabled: true
    limit_per_user: 5

author_weight:
  twitter:
    karpathy: 10
    sama: 9
    default: 5

twitter_accounts:
  - karpathy
  - sama
  - paulg
```

### 用法

```bash
cd ~/projects/info-feed
python3 feed.py                     # 完整链路：召回→排序→输出日报
python3 feed.py --dry-run           # 只看结果不输出
python3 feed.py --sources twitter   # 只跑 Twitter 召回
python3 feed.py --list              # 列出可用源
```

### 加新源

1. 在 `recall/` 新建 `<name>.py`，继承 `BaseRecall`：
```python
class MyRecall(BaseRecall):
    @property
    def source_name(self) -> str: return "myplatform"
    def recall(self, since, limit_per_user=5, **kwargs) -> list[Item]:
        # 实现抓取逻辑
        return [...]
```
2. 在 `config.yaml` 添加对应的 `recall.myplatform` 配置节 + 关注列表 + 权重
3. 自动注册，无需改 feed.py

### Item 统一格式

```python
@dataclass
class Item:
    id: str; title: str; url: str; content: str
    author: str; source: str       # twitter / jike / bilibili / ...
    content_type: str              # longform / short / repost / video / podcast
    created_at: datetime; score: float = 0.0
    extra: dict = {}               # {"likes": N, "retweets": N, ...}
```

## 平台覆盖（2026-05-20 实测）

| 平台 | 工具 | 本服务器状态 | 备注 |
|------|------|-------------|------|
| Twitter/X | `xreach` (`~/.npm-global/bin/xreach`) | ✅ 可用 | 有 auth cookie，9 个监控账号 |
| B站 | RSSHub (`http://192.3.16.123:8280`) | ❌ 未启动 | 启动后自动接管：`docker run -d -p 8280:1200 diygod/rsshub` |
| 小宇宙 | RSS feed / API | ❌ 需 RSSHub | feed.xyzfm.space 返回 404，官方 RSS 废弃 |
| 即刻 | `app.jike.ruguoapp.com` API | ❌ 需配置 UID + token | 在 USERS 列表配好 UID 即可 |
| 公众号 | `wechat-article-exporter` Docker | ✅ 运行中 | 3000 端口，1210 篇文章已存档 |
| RSS/博客 | FreshRSS Docker | ❌ 未启动 | 端口 8386，配好即可 |

**替代方案（商业 API）**: `justoneapi.com` — 支持 Twitter/B站/公众号/微博/小红书/抖音等。按调用量收费。

## Cron 调度

用 Hermes `cronjob` 工具调度，不是系统 crontab：

```bash
# 创建 cronjob（已配置：每天 8:00 / 20:00 抓 Twitter）
cronjob action=create \
  name=info-feed-twitter \
  schedule="0 8,20 * * *" \
  script=run-feed-twitter.sh \
  no_agent=true \
  workdir=/home/wangsiji/projects/info-feed
```

脚本放在 `~/.hermes/scripts/`，内容是调用 `feed.py` 加上参数。

## 输出结构

```
Inbox/_wiki/raw/
├── twitter/2026-05-20.md    ← 当天推文
├── bilibili/2026-05-20.md   ← 当天 B站更新（RSSHub 就绪后）
├── jike/2026-05-20.md       ← 当天即刻动态（配好 UID 后）
└── xiaoyuzhou/2026-05-20.md ← 当天播客更新（RSSHub 就绪后）
```

每篇文件格式：标题 + 元数据行 + 摘要。

## 已知坑（2026-05-20 实测）

### xreach
- `xreach tweets <handle> -n <N>` 返回最近 N 条，包含旧推文（不按时序严格过滤）
- 时间格式：`"Sun May 10 11:08:42 +0000 2026"` → `datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")`
- 字段名：`likeCount`（不是 `favorite_count`）、`screenName`（不是 `screen_name`）
- 纯链接推文：text 字段就是 URL，内容为空

### B站
- 海外服务器 IP 直连 `api.bilibili.com` 被 Cloudflare 412 拦截
- 自建 RSSHub 是唯一可行方案（公共实例也封海外 IP）
- RSSHub Docker 默认镜像没有 Playwright，B站路由需要浏览器渲染

### 即刻
- 即刻 API 需要 `x-jike-access-token` + `x-jike-refresh-token` header
- 需要从浏览器登录即刻后获取 token
- 公开 API `app.jike.ruguoapp.com/1.0/personalUpdate/list` 带 uid 参数可获取用户动态

### 小宇宙
- 官方 RSS feed 已废弃（`xiaoyuzhoufm.com/podcast/{pid}/feed.xml` 返回 404）
- `feed.xyzfm.space/{pid}` 也返回 404
- 需要从 Next.js SPA 的 `__NEXT_DATA__` JSON 中提取数据，或走 RSSHub
- 播客 pid 从 URL `xiaoyuzhoufm.com/podcast/{PID}` 获取

## 扩展指南

**加新平台** = 三步：

1. 在 `providers/` 创建 `<name>.py`，继承 `BaseProvider`：
```python
from .base import BaseProvider, FeedEntry

class MyPlatformProvider(BaseProvider):
    @property
    def name(self) -> str: return "myplatform"

    def fetch(self, limit=10) -> list[FeedEntry]:
        # 实现抓取逻辑
        return [...]
```
2. 在类里定义可配置的账号/频道列表（用户直接在文件里增删）
3. 自动注册，无需修改 `feed.py`

### 小宇宙播客 RSS 发现（重要）

小宇宙页面是 Next.js SPA，RSS URL 不在页面直接暴露。需要从 `__NEXT_DATA__` JSON 中提取：

```python
import re, json
from urllib.request import urlopen, Request

html = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"})).read().decode()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1))
episodes = data["props"]["pageProps"]["podcast"]["episodes"]
# 每期字段: eid, title, description, pubDate, duration, enclosure{url}, playCount
```

podcast ID 从 URL `xiaoyuzhoufm.com/podcast/{PID}` 提取。

**Twitter cookie 获取方式**：在已登录 Twitter 的浏览器 → F12 → Application → Cookies → x.com → 找到 `ct0` 和 `auth_token` 两个值。

**Twitter RSS 解法（RSSHub 需要 cookie）**：
```bash
# 重启 RSSHub 容器并注入 Twitter cookie
sudo docker stop rsshub
sudo docker rm rsshub
sudo docker run -d \
  --name rsshub \
  -p 8280:3000 \
  -e PORT=3000 \
  -e NODE_ENV=production \
  -e TWITTER_COOKIES='{"ct0":"<ct0值>","auth_token":"<auth_token值>","twid":"<twid值>"}' \
  diygod/rsshub:latest
```
获取 cookie 后配置此项，Twitter RSS 路由即可通过 RSSHub 访问。

**B站的问题**：VPS IP 被 B站 识别为数据中心 IP，直接封禁。Playwright 能跑但网络层被封，无法通过 RSSHub 绕过。需要住宅代理或换 IP。
**结论**：B站 RSS 暂时无法自建解决；用户发 B站链接时用 agent-reach 手动抓取。

**问题**: 海外服务器 IP 调用 `api.bilibili.com` 返回 `HTTP 412 Precondition Failed`

**不是 WBI 签名问题**——是 B站对海外 IP 的风控限制，无论是否带 wbi 参数都会 412。

**RSSHub Docker B站 route 也失败**：默认 `diygod/rsshub:latest` 镜像没有 Playwright，B站 route 需要浏览器渲染才能抓取。

**解法**:
- RSSHub 的 B站 route 需要 Playwright，但容器内 `npm install playwright` 因依赖冲突失败
- 用户直接发 B站视频链接 → 手动抓取（可行）
- 不要从 VPS 尝试自动抓 B站

### 微信公众号 ⚠️（2026-05-12 实测）

- **wechat-article-for-ai**: 能抓取，但频繁触发微信验证码（CAPTCHA）→ 需要人工介入
**RSSHub 公共实例**: 全部 503/超时，无法桥接公号 RSS  
**RSSHub Docker 镜像**: `diygod/rsshub:latest`（不是 `rsshub/rsshub:latest`），自带部分路由；B站等需要 Playwright 的 route 暂不可用
### FreshRSS 部署（2026-05-12 实测完成）

✅ **已成功部署并调通**

Docker 部署：
```bash
sudo docker run -d \
  --name freshrss \
  -p 8386:80 \
  -v /home/wangsiji/freshrss/data:/data \
  -e CRON_MIN="*/30" \
  --restart unless-stopped \
  freshrss/freshrss
```

✅ **必须通过安装向导初始化**——无法通过 CLI/API 自动创建管理员账号。  
初始化地址：`http://192.3.16.123:8386` → 选简体中文 → 创建账号 `wangsiji@buaa.edu.cn`

**当前已订阅源**：
- feed/1: FreshRSS releases
- feed/2: 一人公司播客（xiaoyuzhoufm）

**API配置（已调通）**：
1. 右上角用户名 → 设置 → 账户 → 开启「Allow API access」
2. 设置 API 专用密码（不是登录密码）
3. API端点：`http://192.3.16.123:8386/api/greader.php`
4. 认证：两步认证（见下方详细流程）

> 📂 `references/freshrss-api-debugging.md` — FreshRSS Google Reader API 完整调试笔记，包含 Auth Token 获取、URL 格式、PHP 手动计算 Token、订阅操作命令

**API调用格式（正确版）**：
```bash
# Step 1: 获取 Auth Token（POST）
TOKEN=$(curl -s -X POST "http://192.3.16.123:8386/api/greader.php/accounts/ClientLogin" \
  -d "Email=wangsiji@buaa.edu.cn&Passwd=<API密码>" | grep "^Auth=" | cut -d= -f2)

# Step 2: 使用 Token（Authorization header）
curl -s -H "Authorization: GoogleLogin_auth=$TOKEN" \
  "http://192.3.16.123:8386/api/greader.php/reader/api/0/subscription/list?output=json"
```

⚠️ **关键坑**：
- 路径是 `/reader/api/0/...`（不是 `/api/0/...`，也不是 `/greader.php/api/0/...`）
- Authorization 是 `GoogleLogin_auth=<token>`，不是 Basic Auth
- Token 格式是 `email/sha1(salt+email+hash)`，不是直接密码

### 关键坑：去重查询 bug（2026-05-12 实测）

**错误代码**:
```python
# ❌ 错误：conn.execute() 返回 cursor 对象，if 判断永远为 truthy
if conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id=?"):
    continue
# ✅ 正确：必须调用 .fetchone()
if conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id=?").fetchone():
    continue
```

**症状**: 第二次运行仍然返回所有推文（不去重），数据库里也没有记录增长。

**修复**: 所有去重查询必须加 `.fetchone()`。

### 关键坑：回复要结论先行，不要解释过程

**用户反馈**："这个方案有问题：..." → 用户主动纠正了我先说方案再说问题的顺序。

**正确做法**：
- ❌ "我来试试A方法...不行...再试B方法...也不行...结论是用C"（被纠正）
- ✅ "结论：Folo无法通过API获取，它是闭源SaaS。原因是..."（一次说清）

在涉及技术可行性的回答中，**先给结论，再给原因，最后问要不要继续**。

### MiniMax API 调用格式（实测修正 2026-05-12）

```python
import urllib.request, json

API_KEY = "sk-cp-pkBPNfAY97fHhEFlnUCCMNYeEigMzLlSWryR_eaMjHIFFkNFnPjrEJURx_hmSkX4FQFf-PX5df4em2f2ehwNRigAlgem8SfjdHez6iyplTdaFN_HG-9bZ7o"
API_BASE = "https://api.minimaxi.com/anthropic/v1"

def llm_summary(prompt: str) -> str:
    payload = {
        "model": "MiniMax-M2",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    req = urllib.request.Request(
        f"{API_BASE}/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        # ⚠️ 正确格式：content 在顶层，不是 choices 路径
        # 返回结构: {"content": [{"type":"thinking","..."}, {"type":"text","text":"..."}]}
        for item in data.get("content", []):
            if item.get("type") == "text":
                return item["text"]
        return str(data.get("content", ""))
```

⚠️ **之前错误**：用 `data["choices"][0]["message"]["content"]`
⚠️ **正确格式**：`data["content"]` 是顶层 list，找 `type=="text"` 的项

## 已有的采集工具

| 平台 | 工具 | 命令 |
|------|------|------|
| 推特 | xreach | `xreach home --format json` / `xreach list-tweets <url>` |
| 推特关注列表 | xreach | `xreach following <handle>` — 获取指定账号关注的所有人（47个账号全量拉取成功） |
| 推特推文归档 | xreach | `xreach tweet <id>` — 单条推文内容，输出 JSON |
| 公众号 | wechat-article-for-ai | `python3 ~/.agent-reach/tools/wechat-article-for-ai/main.py <url>` |
| RSS | feedparser | `pip install feedparser` |

## 采集工具坑

- **wechat-article-for-ai 的 BS4 4.14.3 兼容 bug**：soup.new_tag() 在 lxml 解析器下返回 None，修法是建一个独立 BS("", "html.parser") 实例来 new_tag
- **xreach JSON 格式**：
  - `xreach following <handle>`：响应结构是 `{"items": [...]}`，不是直接数组，解析用 `data.get('items', [])`
  - `xreach tweet <id>`：响应是直接对象，不是数组
  - 字段名：点赞用 `likeCount`（不是 `favorite_count`），作者用 `screenName`（不是 `screen_name`），粉丝用 `followersCount`
  - Tweet URL 构造：`https://x.com/{screenName}/status/{id}`
  - 推文全文在 `text` 字段，媒体在 `media` 数组（每项含 `url`）
  - 纯链接推文：有些推文只发链接（如 `https://t.co/xxx`），text 字段就是 URL，内容为空
- **xreach cookie 认证**：需要先 `xreach auth` 配置 Cookie 才能抓数据
- **小宇宙播客**：纯链接推文的 text 就是 URL，内容为空
- **MiniMax API**：返回 content 是数组，需遍历找 `type=="text"`

## LLM 配置（MiniMax）

MiniMax API 兼容 OpenAI 格式，但 endpoint 不同：

```python
url = "https://api.minimaxi.com/anthropic/v1/messages"  # 而非 api.openai.com
model = "MiniMax-M2.7"  # 或 MiniMax-M2.5
```

MiniMax API Key 从 `~/.hermes/.env` 里的 `MINIMAX_CN_API_KEY` 获取（key 被 `***` 遮住，需要用户手动提供）。

### 调研方法：GitHub 搜索策略（2026-05-12 新增）

当用户要求「去 GitHub 搜索 XX 工具」时：

```bash
# 搜索已知的商业 API 聚合器
curl -s "https://api.github.com/search/repositories?q=weibo+bilibili+twitter+api+python&sort=stars&per_page=15"

# 搜索 RSSHub 生态
curl -s "https://api.github.com/search/repositories?q=rsshub+ecosystem+follow+reader"

# 搜索通用社交媒体聚合器
curl -s "https://api.github.com/search/repositories?q=social+feed+aggregator+api+nodejs&sort=stars"
```

**搜索技巧**：
- GitHub 搜索 `site:github.com <关键词>` 在浏览器更好用
- 按 stars 排序能找到社区认可的真实方案
- 0 results 不代表没有，可能是关键词不对

**发现的商业方案**：
- **justoneapi** (⭐148) — Python SDK，聚合 Twitter/小红书/抖音/微博/B站/微信公众号等几十个平台。注册地址：dashboard.justoneapi.com。**这是目前唯一找到的支持全平台的免费/商业混合方案**。但它本质是商业 API（按调用量收费），不是自建方案。

## 调研发现的参考项目

| 项目 | 技术栈 | 亮点 |
|------|--------|------|
| [cartero](https://github.com/dracarys18/cartero) | Go + SQLite | 配置驱动，RSS/HN/Lobsters → Discord/Feed，支持多目标 |
| [ailert](https://github.com/anuj0456/ailert) | Python + Flask + DynamoDB | 150+ 源，async 处理，newsletter 生成，Section 概念 |
| DevDigestAI | LLM + RSS | GitHub Actions 定时任务，开发者新闻聚合 |

## 输出形态
- Telegram digest（最轻量）
- Obsidian 存档（方便后续检索）
- 或者两者都要

## xreach tweets 命令详解

`xreach tweets <handle>` 是获取某账号推文的核心命令：

```bash
# 基本用法（输出 JSON）
xreach tweets paulg --count 20 --plain

# 选项
--count <n>      每页条数（默认20）
--replies       包含回复
--max-pages <n> 最多页数（默认1）
```

**JSON 输出格式**：
```json
{
  "items": [
    {
      "id": "2053432032621965741",
      "text": "推文内容",
      "createdAt": "Sun May 10 11:08:42 +0000 2026",
      "user": {
        "screenName": "paulg",
        "name": "Paul Graham"
      },
      "likeCount": 2995,
      "retweetCount": 174,
      "replyCount": 175,
      "viewCount": 140333,
      "isRetweet": false,
      "lang": "en"
    }
  ],
  "cursor": "DAAH...",
  "hasMore": true
}
```

**关键坑**：
- 字段名是 `likeCount`（不是 `favorite_count`）、`screenName`（不是 `screen_name`）
- 时间格式：`"Sun May 10 11:08:42 +0000 2026"` → Python `datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")`
- `--format json` 不生效，始终用 `--plain`（输出本身就是 JSON）
- `--limit` 参数不存在，用 `--count`
- 纯链接推文的 `text` 就是 URL，内容为空

## Cron 调度

用 Hermes `cronjob` 工具调度，不是系统 crontab：

```bash
# 创建 cronjob（已配置：每天 8:00 / 20:00 抓 Twitter，仅 Twitter 可用）
cronjob action=create \
  name=info-feed-twitter \
  schedule="0 8,20 * * *" \
  script=run-feed-twitter.sh \
  no_agent=true \
  workdir=/home/wangsiji/projects/info-feed
```

脚本放在 `~/.hermes/scripts/`，内容是调用 `feed.py` 加上参数。添加新源时创建新脚本 + 新 cronjob。

## 关键坑（实测）

- **xreach JSON 格式**：
  - `xreach following <handle>`：响应结构是 `{"items": [...]}`，不是直接数组
  - `xreach tweet <id>`：响应是直接对象，不是数组
  - 字段名：点赞用 `likeCount`，作者用 `screenName`
- **xreach `--limit` 不存在**，用 `--count`
- **xreach `--format json` 不生效**，始终用 `--plain`
- **时间格式**：`"Sun May 10 11:08:42 +0000 2026"` → `datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")`
- **纯链接推文**：text 字段就是 URL（如 `https://t.co/xxx`），内容为空
- **X Premium 内容**：链接是 `x.com/i/article/xxx` 格式的是付费内容，无法获取正文，只能归档元数据
- **去重数据库**：第一次跑会抓到所有历史推文（因为 xreach 只返回最近20条），第二次跑只会抓到新增的。运行前先清空 `seen_tweets` 表可以重置状态。

## 用户交互协议

用户收到 digest 后，回复格式：
- `保留 3` → 归档第3条到 wiki + 询问用户注解
- `保留 1,3,5` → 同时归档多条
- `跳过` → 丢弃，结束本轮

## 行动指引
1. 用户明确要求**不添加过滤规则，全部保存**（cutoff 窗口=24小时即可）
2. 搭 SQLite 去重表（seen_tweets: tweet_id + handle）
3. 输出双格式：`tweets.json` + `tweets.md`
4. 定时 cron → 凌晨1点运行（`0 1 * * *`）+ 早上9点 digest（`0 9 * * *`）
