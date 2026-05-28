---
name: info-recommendation-system
description: Build multi-source information input systems with recall→ranking→output architecture. Twitter/即刻/B站/小宇宙/公众号 ingestion, content scoring, daily digests.
category: productivity
---

# Information Recommendation System

Build a personalized information input pipeline with a classic recommendation system architecture:

```
Data Sources → Multi-Channel Recall → Ranking → Daily Digest
```

## Architecture

```
project/
├── config.yaml              # All config: sources, weights, time window
├── feed.py                  # Entry point: recall → rank → output
recall/
│   ├── base.py              # BaseRecall + Item dataclass
│   ├── twitter.py           # xreach-based Twitter recall
│   ├── bilibili.py          # bilibili-api-python + curl_cffi (bypasses Cloudflare directly)
│   ├── jike.py              # 即刻 via RSSHub
│   └── xiaoyuzhou.py        # 小宇宙 via RSSHub
└── ranking/
    ├── engine.py            # Scoring engine
    └── features.py          # Feature computation
```

## Key Components

### 1. BaseRecall Class (`recall/base.py`)

Every recaller inherits `BaseRecall` and implements:
- `source_name` (property): source identifier
- `recall(self, since, **kwargs)`: returns list of `Item`

`Item` dataclass fields:
- `id`, `title`, `url`, `content`, `author`, `source`, `content_type`
- `created_at`, `score`, `extra` (likes/retweets/replies)

### 2. Content Item Schema

```python
@dataclass
class Item:
    id: str
    title: str
    url: str
    content: str
    author: str
    source: str          # twitter / jike / weixin / bilibili / xiaoyuzhou
    content_type: str    # longform / short / repost / video / podcast
    created_at: datetime
    score: float
    extra: dict          # engagement metrics
```

### 3. Ranking Formula

```
score = author_weight × content_type_weight × recency_decay + engagement_bonus
```

Where:
- **author_weight**: configurable per source/author (1-10 scale, normalized to 0.5-2.0)
- **content_type_weight**: longform=1.3, podcast=1.2, video=1.1, short=1.0, repost=0.7
- **recency_decay**: `2^(-hours_ago / half_life_hours)` — half_life defaults to 8h
- **engagement_bonus**: `log2(1 + likes + retweets + replies) × 0.1`

### 4. Config Pattern (`config.yaml`)

```yaml
recall:
  twitter:
    enabled: true
    limit_per_user: 5
  jike:
    enabled: true
    limit_per_user: 5
  # ... per-source config

author_weight:
  twitter:
    karpathy: 10
    sama: 9
    default: 5
  # ... per-source author weights

content_type_weight:
  longform: 1.3
  short: 1.0

recency:
  half_life_hours: 8

output:
  top_k: 30
  min_score: 1.0
  obsidian_path: "~/path/to/vault/Inbox/_wiki/raw"
```

### 5. Cron Setup

Run daily at 8:00 and 20:00 Beijing time:

```bash
# Script at ~/.hermes/scripts/run-feed-rss.sh
cd /home/wangsiji/projects/info-feed
python3 feed.py
```

Cron job config: `0 8,20 * * *`, no_agent=True, script runs the bash wrapper.

## Adding a New Source

1. Create `recall/newsource.py` inheriting `BaseRecall`
2. Implement `source_name` and `recall()` method
3. Add config section to `config.yaml` (enabled, accounts, weights)
4. No registration needed — `feed.py` auto-discovers recallers via pkgutil

## Content Strategy: 秋秋双账号 Ecosystem

The info-feed system ingests data from two personal WeChat accounts, among others. The following framework governs content strategy decisions — which account a topic belongs on, what angle to take, and how AI content fits into a non-AI brand.

See `references/qiuyu-content-strategy.md` for the full reference (content positioning, brand strategy, AI-content filtering frame, account statistics, vector DB labeling history).

### Quick Decision Table

| Topic | 秋秋很开心 | 秋秋在分享 |
|-------|-----------|-----------|
| FIRE财务实操、存钱、投资、4%法则 | ✗ | ✅ 核心品牌 |
| 学习方法、手帐、效率、APP推荐 | ✅ 核心品牌 | ✗ |
| AI工具评测、Prompt技巧 | ✗ (除非个人实践视角) | ✗ |
| 社会评论 | ✗ | ✗ |

**AI content filter** — ask: "把AI换成任何其他工具，这篇文章还成立吗？"
- 成立 (focus on personal practice) → 秋秋很开心
- 不成立 → neither account fits; this topic isn't right for 秋秋

### Vector DB Account Labeling (Critical)

When rebuilding the vector index for 4+ accounts (秋秋很开心, 秋秋在分享, 数字生命卡兹克, 六镇), match directory names precisely:

```python
if "秋秋很开心" in fp_str: account = "秋秋很开心"
elif "秋秋在分享" in fp_str: account = "秋秋在分享"
elif "数字生命卡兹克" in fp_str: account = "数字生命卡兹克"
elif "六镇" in fp_str: account = "六镇"
```

**Always verify after rebuild** by checking account distribution via `collection.get(include=['metadatas'])`. Cross-check against raw `ls` counts — DB aggregations can mislead when labeling is wrong.

## Content Knowledge Base (Semantic Search)

When you have a scraped content archive (e.g., WeChat articles), build a vector search index to query semantically instead of grep:

```bash
cd ~/projects/info-feed
python3 build_index.py                # Build/rebuild index
python3 build_index.py --query "query" # Search
python3 build_index.py --stats        # Show stats
```

Uses ChromaDB + all-MiniLM-L6-v2. Full technique: `references/vector-search-knowledge-base.md`.

### Agent-Integrated Semantic Search (Conversational)

For agents (Hermes, etc.) that need to query the knowledge base mid-conversation without switching to a shell, use `qiuyu_search.py` — a JSON-output wrapper around the same ChromaDB index:

```bash
# Terminal from agent context
cd /home/wangsiji/projects/info-feed
source .venv/bin/activate
python3 qiuyu_search.py "FIRE 财务自由 4%法则"
```

Returns structured JSON:
```json
{
  "query": "FIRE 财务自由",
  "count": 10,
  "results": [
    {
      "title": "每个人都能财务自由",
      "account": "秋秋在分享",
      "url": "https://mp.weixin.qq.com/s/...",
      "pub_date": "2026-04-27 10:49",
      "score": 0.52,
      "preview": "片段预览（300字）",
      "full_text": "完整段落文本"
    }
  ]
}
```

**Integration pattern for agent conversations**: When the user asks "秋秋之前写过XX吗" or "秋秋有没有写过XX", the agent should:
1. Call `terminal()` with the `qiuyu_search.py` command (must use `.venv/bin/activate` for chromadb import)
2. Parse the JSON results
3. Present top matches with title, score, URL, and a brief preview
4. Follow up with deeper reading if user wants

The `qiuyu` CLI at `~/.local/bin/qiuyu` is a bash wrapper around `build_index.search()`. For agent use, prefer `qiuyu_search.py` which returns JSON. Full integration setup: `references/qiuyu-search-integration.md`.

## Platform Notes

### Twitter
- Uses `xreach` CLI (must be authenticated)
- Rate limit: 1.5s delay between user fetches
- Content types: short (<500 chars), longform (>=500 chars), repost

### B站 (Bilibili)

**Primary approach (recommended)**: Use `bilibili-api-python` + `curl_cffi` directly — bypasses B站's Cloudflare without RSSHub.
See `references/bilibili-api-notes.md` for full technique (UID lookup, rate limiting strategy, cookie-based credential auth).

```bash
pip install bilibili-api-python curl_cffi
```

**Critical: Provide B站 login cookies for ~100% success rate.** Without SESSDATA/buvid3, ~50% of requests get 412'd from datacenter IPs. Cookie export format and setup documented in `references/bilibili-api-notes.md`.

```python
from bilibili_api import Credential, user

cred = Credential(
    sessdata="...", bili_jct="...",
    dedeuserid="...", buvid3="...", buvid4="...",
)
u = user.User(uid, credential=cred)
data = await u.get_videos(ps=10, pn=1)
```

Key patterns:
- **Request delay**: 5s + random jitter between each UP主 fetch (B站 412 rate limits are aggressive)
- **Retry**: 412 errors should trigger a retry after 15s delay (rare with cookies, but safe)
- **Content detection**: filter by `created >= since_ts` to get only recent videos
- **Fields available**: title, bvid, created (unix ts), play/comment/danmaku counts, length (mm:ss), description, pic (thumbnail), author name

**Fallback**: RSSHub Docker at port 8280 (route: `/bilibili/user/video/:mid`). Unreliable from datacenter IPs — Cloudflare blocks most server IP ranges. Even Playwright headless browser inside RSSHub may fail.

**Alternative (one-off transcription)**: Get笔记 API (`getnote`) for transcribing individual B站 videos to text. Requires `GETNOTE_API_KEY` and `GETNOTE_CLIENT_ID`. Used by qiaomu-anything-to-notebooklm project. Not suitable for continuous monitoring.

### 即刻 (Jike)
- Requires RSSHub
- UID from user profile URL: `https://web.okjike.com/u/{uid}`
- Public API via RSSHub returns limited data

### 小宇宙 (Xiaoyuzhou)
- Requires RSSHub
- PID from podcast page URL: `xiaoyuzhoufm.com/podcast/{pid}`
- Returns full episode descriptions and audio links

## Paywall Bypass (Optional Enhancement)

For paywalled article links found in Twitter/X feeds, a 6-level cascading bypass system is documented in `references/paywall-bypass-cascade.md`. This is a self-contained shell script pattern (no Python dependencies) that can extract content from 300+ paywalled sites including NYT, WSJ, FT, Economist, Bloomberg. Useful when the daily digest should include full article summaries from paywalled links.

## Public-Facing Website (Static Timeline)

Generate a public-facing timeline website from the info-feed data. Hosted at `https://wangsiji.site/feed/`, auto-updated after each cron run.

### Architecture

```
~/projects/aihot-local/
├── generate.py           # Static site generator (reads feed data, renders HTML)
├── templates/
│   └── index.html        # Dark theme timeline template with filters
└── output/               # Local backup of generated files
```

The generator reads from the recallers (same as `feed.py`), builds a unified timeline, and renders static HTML. Output syncs to `/var/www/info-feed/` which nginx serves at `/feed` (no auth).

### Cron Schedule

Feed data collection runs at 8:00 / 20:00 Beijing time. Website generation runs **30 min later** (8:30 / 20:30) so new data is available before the generator runs.

Cron setup:
```
cd ~/projects/aihot-local && python3 generate.py && rsync -a output/ /var/www/info-feed/
```

### Template Features

- Dark theme, responsive
- Category badges: Twitter (blue), 长文 (green), 播客 (purple)
- JavaScript category filter (All / Twitter / 长文 / 播客)
- Item cards with title, author, preview content, timestamp, and links to source
- Paginated or scrollable timeline view

### Design Decisions

- **Static HTML**: No backend needed, nginx serves as-is, fast and reliable
- **Separate project** from the feed pipeline (info-feed/): the feed system owns data collection + ranking, the website owns presentation. Clean separation of concerns.
- **Template placeholder for items**: `{% for item in items %}` -> `{{ item.title }}`, `{{ item.content }}`, `{{ item.author }}`, `{{ item.source }}`, `{{ item.created_at }}`, `{{ item.url }}`, `{{ item.content_type }}`
- **nginx config**: Auth disabled for `/feed` location (overrides the root domain's basic auth). Uses `alias` not `root` to avoid path prefix issues. See `templates/feed-nginx-location.md`.

### Adding New Data Sources to the Website

1. Ensure the data source is ingested by the info-feed system's recallers
2. `generate.py` auto-discovers available data sources
3. Format items according to the common `Item` dataclass schema
4. No template changes needed (categories are auto-detected from `content_type`)

See `templates/feed-website-index.html` for the full dark-theme timeline template.

## Pitfalls

- **Rate limiting**: Twitter API has per-endpoint limits; B站 API aggressive against datacenter IPs — use 5s+ delay with jitter and retry logic
- **Time windows**: recallers filter by `created_at >= since` — data older than time_window_hours is dropped
- **B站 412 与 cookie 过期**: Use `bilibili-api-python` library which handles WBI signing internally. Direct curl to `api.bilibili.com` will fail with -352 (风控校验失败). Add 5s delay between UP主s, retry on 412 after 15s. SESSDATA expires ~30 days — refresh by re-exporting cookies from browser.
- **Vector DB account labeling**: See the "Content Strategy" section above for correct multi-account labeling and post-rebuild verification. TL;DR: match directory names precisely, verify via `collection.get(include=['metadatas'])`, and cross-check against raw `ls` counts.
- **Item dedup**: `feed.py` deduplicates by item.id across all recallers
