#!/usr/bin/env python3
"""
Twitter Morning Digest — reads last night's fetch, pushes top tweets to Telegram.
User replies "keep N" to archive with personal reflection.

Cron: 0 9 * * *
"""

import json, subprocess, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

VAULT_BASE = Path("/home/wangsiji/projects/wsj-second-brain/Inbox/_wiki")
TWEETS_DIR = VAULT_BASE / "raw" / "tweets"
STATE_DB   = VAULT_BASE / "scripts" / "fetch_state.db"

# ── Find latest fetch file ────────────────────────────────────────────────────

def latest_fetch():
    dirs = sorted([d for d in TWEETS_DIR.iterdir() if d.is_dir() and d.name.startswith("2026")])
    return dirs[-1] if dirs else None

# ── Pick top tweets ─────────────────────────────────────────────────────────

def top_tweets(tweets, max_tweets=12):
    """Pick diverse high-value tweets across accounts."""
    scored = []
    for t in tweets:
        score = t["like_count"] * 2 + t["retweet_count"] + t["view_count"] // 1000
        if not t.get("is_retweet"):
            score += 50  # Boost original tweets
        scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Deduplicate by handle (max 2 per handle)
    selected, seen = [], {}
    for score, t in scored:
        if len(selected) >= max_tweets:
            break
        h = t["handle"]
        if seen.get(h, 0) >= 2:
            continue
        seen[h] = seen.get(h, 0) + 1
        selected.append(t)

    return selected

# ── Format digest ────────────────────────────────────────────────────────────

def format_digest(tweets, fetch_date: str, total: int) -> str:
    lines = [
        f"📥 Twitter 日报 · {fetch_date}",
        f"共抓到 {total} 条，摘要如下：",
        "",
    ]
    for i, t in enumerate(tweets, 1):
        txt = t["text"]
        if len(txt) > 200:
            txt = txt[:200].rsplit(" ", 1)[0] + "…"
        txt = txt.replace("\n", " ").strip()
        lines.append(f"{i}. @{t['handle']}（{t['name']}）")
        lines.append(f"   {txt}")
        lines.append(
            f"   🔗 https://x.com/{t['handle']}/status/{t['id']} "
            f"· {t['like_count']}❤ {t['view_count']}👁"
        )
        lines.append("")

    lines += [
        "---",
        "回复「保留 1」「保留 2」… 归档到 wiki（自动附链接）。",
        "只保留有用的，拒绝噪声。",
    ]
    return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────

fetch_dir = latest_fetch()
if not fetch_dir:
    print("No fetch data found, skip.")
    sys.exit(0)

json_file = fetch_dir / "tweets.json"
if not json_file.exists():
    print(f"No tweets.json in {fetch_dir}, skip.")
    sys.exit(0)

with open(json_file) as f:
    data = json.load(f)

tweets = data.get("tweets", [])
total  = data.get("total_new", len(tweets))
fetch_date = data.get("date", fetch_dir.name)

selected = top_tweets(tweets)
digest   = format_digest(selected, fetch_date, total)

dig_file = fetch_dir / "digest.md"
with open(dig_file, "w") as f:
    f.write(digest)

print(f"TWEETS_TOTAL={total}")
print(f"TWEETS_SELECTED={len(selected)}")
print(f"DIGEST_FILE={dig_file}")
print()
print(digest)
