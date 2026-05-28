# xreach API 推文搜索 + 剪藏工作流

搜索 Twitter 上高互动推文，直接格式化为 Obsidian Markdown 保存到 vault。

## 场景

- 搜索特定主题的高互动推文并批量剪藏
- 单条热门推文归档
- 需要保留互动数据（点赞/转发/收藏数）作为 note 元信息

## 前置条件

```bash
xreach auth check
# ✓ Authenticated
```

## 完整流程

### 1. 搜索推文并过滤高互动内容

```bash
# 搜索，按互动量排序
xreach search "obsidian web clipper" -n 30 2>&1 | python3 -c '
import json, sys
data = json.load(sys.stdin)
tweets = data.get("items", [])
tweets.sort(key=lambda t: -(t.get("likeCount",0) + t.get("retweetCount",0) + t.get("bookmarkCount",0)))
for t in tweets[:10]:
    text = t.get("text", "")[:120].replace("\n", " ")
    print(f'ID: {t["id"]} | 👍{t.get("likeCount",0)} 🔁{t.get("retweetCount",0)} 🔖{t.get("bookmarkCount",0)}')
    print(f'  {text}')
'
```

### 2. 获取单条推文详情（含用户信息）

```bash
xreach tweet POST_ID --json
```

返回结构示例：
```json
{
  "id": "2052720961531879779",
  "text": "这三个东西凑齐之后...",
  "createdAt": "Fri May 08 12:03:09 +0000 2026",
  "user": {
    "id": "VXNlcjoxOTMyOTM1NzA1NzExNTEzNjAw",
    "restId": "1932935705711513600",
    "name": "Yanhua",
    "screenName": "yanhua1010",
    "isBlueVerified": true
  },
  "replyCount": 48,
  "retweetCount": 210,
  "likeCount": 1057,
  "bookmarkCount": 1818,
  "lang": "zh",
  "isRetweet": false
}
```

⚠️ **注意**：`xreach tweet POST_ID`（无 `--json`）返回纯文本版，内容可能被截断。勾选 `--json` 获得完整结构。

### 3. 格式化为 Obsidian 笔记（Python 模板）

```python
import json, subprocess, re
from datetime import date

def clip_tweet(tweet_id: str, output_dir: str = "/home/wangsiji/projects/wsj-second-brain/Clippings"):
    """获取一条推文并保存为 Obsidian Markdown"""
    r = subprocess.run(["xreach", "tweet", tweet_id, "--json"],
        capture_output=True, text=True, timeout=15)
    t = json.loads(r.stdout)

    text = t.get("text", "")
    user = t.get("user", {})
    sn = user.get("screenName", "?")

    today = date.today().isoformat()
    created = t.get("createdAt", "unknown")

    note = f"""---
title: {text[:60].strip()!r}
source: https://x.com/{sn}/status/{tweet_id}
domain: x.com
clipped: {today}
author: "@{sn} ({user.get('name', '?')})"
created: {created}
engagement:
  likes: {t.get('likeCount', 0)}
  retweets: {t.get('retweetCount', 0)}
  bookmarks: {t.get('bookmarkCount', 0)}
  replies: {t.get('replyCount', 0)}
---

## 原文内容

{text}

---
*剪藏自 X/Twitter | 互动: 👍{t.get('likeCount',0)} 🔁{t.get('retweetCount',0)} 🔖{t.get('bookmarkCount',0)}*
"""

    safe = re.sub(r'[\\/:*?"<>|]', '_', text[:60]).strip()
    safe = re.sub(r'\s+', '_', safe)
    path = f"{output_dir}/{safe}.md"
    with open(path, "w") as f:
        f.write(note)
    print(f"✅ Saved: {path}")
    return path

# 使用
clip_tweet("2052720961531879779")
```

### 4. 批量剪藏

```python
tweet_ids = [
    "2052720961531879779",  # 高互动推文1
    "2042964631098904603",  # 高互动推文2
]
for tid in tweet_ids:
    clip_tweet(tid)
```

## 保存目录

- 推文：`~/projects/wsj-second-brain/Clippings/`
- X Article：`~/projects/wsj-second-brain/Inbox/LLM-WiKi/Raw/Clippings/`

## 已剪藏记录

| 日期 | 推文 | 作者 | 互动 |
|------|------|------|------|
| 2026-05-27 | "三个东西凑齐之后，Obsidian已经不是一个笔记软件了" | @yanhua1010 | 👍1057 🔖1818 |
| 2026-05-27 | "58页的Obsidian+Claude Code构建知识库的橙皮书" | @AlchainHust | 👍1102 🔖1558 |
| 2026-05-27 | "one underrated obsidian use case: memory layer" | @EXM7777 | 👍484 🔖748 |
| 2026-05-27 | "沉浸式油管学习方案" (Obsidian Web Clipper) | @xiangxiang103 | 👍771 🔖1488 |
| 2026-05-27 | "OBSIDIAN JUST TURNED THE ENTIRE INTERNET INTO A STRUCTURED MEMORY SYSTEM" | @DamiDefi | 👍143 🔖103 |
| 2026-05-27 | "分享个爽用的插件 Obsidian Web Clipper" | @noahduck283 | 👍9 🔖17 |
