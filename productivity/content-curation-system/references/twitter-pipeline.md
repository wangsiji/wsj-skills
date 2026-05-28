# Twitter Pipeline Reference

> 2026-05-12 | 完整实现跑通，统一脚本已升级为 daily-digest.py

## 脚本位置

```
Inbox/_wiki/scripts/
├── daily-digest.py       # 统一脚本：Twitter+B站+播客+AI摘要（生产用）
├── twitter-fetch.py     # Twitter专用（早期版本，仍可用）
├── twitter-digest.py    # Twitter专用精选（早期版本，仍可用）
├── wechat-fetch.py      # 微信公众号（待接入）
└── fetch_state.db       # SQLite去重数据库
```

**执行**：`cd /home/wangsiji/projects/wsj-second-brain/Inbox/_wiki && python3 scripts/daily-digest.py`

**Cron**：`0 1 * * *`（凌晨1点采集）+ `0 9 * * *`（早上9点推送）

## 去重数据库

- 位置：`Inbox/_wiki/scripts/fetch_state.db`（SQLite）
- 表：`seen_tweets(tweet_id TEXT PK, handle TEXT, fetched TIMESTAMP)`
- **⚠️ 去重 bug 已修复**：查询必须加 `.fetchone()`，否则永远不去重
- 重新抓取历史：`DELETE FROM seen_tweets`

## xreach 命令

```bash
# 获取用户推文
xreach tweets <handle> --count 20 --plain
# 返回: {"items": [...]}，每条字段:
#   id, text, createdAt ("Sun May 10 11:08:42 +0000 2026"),
#   user: {screenName, name},
#   likeCount, retweetCount, replyCount, viewCount,
#   isRetweet, isReply, lang, media[]
# ⚠️ Rate limit: 频繁调用会 "Rate limit exceeded"，间隔5分钟以上
```

## 数据格式

```json
{
  "date": "2026-05-12",
  "twitter": {"count": 32, "items": [...]},
  "bilibili": {"count": 0, "items": []},
  "podcast": {"count": 1, "items": [...]}
}
```

## 用户交互流程

```
凌晨1:00  抓取 → JSON 存档（不打扰）
早上9:00  推送 AI 精选摘要
          ↓
用户用10分钟过一遍
          ↓
回复「保留 3」「保留 7」...
          ↓
没用上的 → 当天丢弃（正确行为）
```

## ⚠️ 已知坑

1. **去重 bug**：`conn.execute("SELECT...").fetchone()` 缺 `.fetchone()` 会导致去重失效
2. **xreach Rate Limit**：两次调用间隔至少5分钟，否则返回 "Rate limit exceeded"
3. **MiniMax API 格式**：`data["content"]` 是 list 不是 `data["choices"][0]["message"]["content"]`
4. **B站 412**：海外IP被B站风控，VPS上无法自动抓B站视频
