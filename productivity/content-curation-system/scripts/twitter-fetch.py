#!/usr/bin/env python3
"""
Twitter Daily Fetcher for @wangcc_ps following list.
Fetches tweets from all 47 followed accounts (last 24h), saves to JSON + Markdown.
Scheduled: cron '0 1 * * *'

Usage:
    cd /path/to/vault/Inbox/_wiki && python3 scripts/twitter-fetch.py

Config:
    VAULT_BASE  — vault root (default: /home/wangsiji/projects/wsj-second-brain/Inbox/_wiki)
    TWEETS_DIR  — where raw tweets go (VAULT_BASE / raw / tweets)
    CUTOFF_HOURS — how far back to fetch (default: 24)
    HANDLES     — list of Twitter handles to fetch

Output:
    raw/tweets/YYYY-MM-DD/tweets.json   ← raw data (for programs)
    raw/tweets/YYYY-MM-DD/tweets.md     ← human-readable digest
    scripts/fetch_state.db              ← SQLite deduplication
    scripts/fetch.log                   ← run log
"""

import json
import subprocess
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

VAULT_BASE = Path("/home/wangsiji/projects/wsj-second-brain/Inbox/_wiki")
TWEETS_DIR = VAULT_BASE / "raw" / "tweets"
STATE_DB   = VAULT_BASE / "scripts" / "fetch_state.db"
LOG_FILE   = VAULT_BASE / "scripts" / "fetch.log"

HANDLES = [
    "whyyoutouzhele","meshtimes_","xiaolai","TheAITimeline","trq212",
    "paulg","bcherny","claudeai","OdysseysEth","XiaohuiAI666",
    "waylybaye","Svwang1","yihong0618","dontbesilent","lxfater",
    "xiaohu","op7418","AI_Jasonyu","gefei55","yihui_indie",
    "turingou","vasuman","0xROAS","MengTo","marclou",
    "steipete","sitinme","binghe","tychozzz","Khazix0918",
    "thedankoe","dotey","lidangzzz","vista8","FuSheng_0306",
    "obsdmd","naval","knowledgefxg","lifesinger","lijigang",
    "idoubicc","sama","jike_collection","AlchainHust","oran_ge",
    "karpathy","kepano",
]

CUTOFF_HOURS = 24

# ── Helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_xreach(args: list[str], timeout: int = 60) -> dict | None:
    cmd = ["xreach"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception as e:
        log(f"ERROR xreach {' '.join(args)}: {e}")
    return None

def init_db():
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_tweets (
            tweet_id TEXT PRIMARY KEY,
            handle   TEXT,
            fetched  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def is_seen(conn, tweet_id: str) -> bool:
    cur = conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id = ?", (tweet_id,))
    return cur.fetchone() is not None

def mark_seen(conn, tweet_id: str, handle: str):
    conn.execute(
        "INSERT OR IGNORE INTO seen_tweets (tweet_id, handle) VALUES (?, ?)",
        (tweet_id, handle)
    )

def fetch_user_tweets(handle: str, cutoff: datetime) -> list[dict]:
    data = run_xreach(["tweets", handle, "--count", "20", "--plain"])
    if not data or "items" not in data:
        return []

    tweets = []
    for t in data["items"]:
        try:
            created = datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")
        except Exception:
            continue
        if created < cutoff:
            continue

        tweets.append({
            "id":            t["id"],
            "text":          t.get("text", ""),
            "created_at":     t["createdAt"],
            "handle":        t["user"]["screenName"],
            "name":          t["user"]["name"],
            "like_count":    t.get("likeCount", 0),
            "retweet_count": t.get("retweetCount", 0),
            "reply_count":   t.get("replyCount", 0),
            "view_count":    t.get("viewCount", 0),
            "is_retweet":    t.get("isRetweet", False),
            "lang":          t.get("lang", "en"),
            "url":           f"https://x.com/{t['user']['screenName']}/status/{t['id']}",
        })
    return tweets

def tweets_to_markdown(tweets: list[dict]) -> str:
    """Render a list of tweets as a Markdown section grouped by handle."""
    lines = [
        f"# Twitter 抓取报告 — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"**抓取窗口**：过去{CUTOFF_HOURS}小时 | **新推文**：{len(tweets)}条",
        "",
    ]

    by_handle = defaultdict(list)
    for t in tweets:
        by_handle[t["handle"]].append(t)

    for handle in sorted(by_handle.keys(), key=lambda h: -len(by_handle[h])):
        ts = by_handle[handle]
        name = ts[0]["name"]
        lines.append(f"## @{handle}（{name}）")
        for t in ts:
            text = t["text"]
            if len(text) > 300:
                text = text[:300] + "…"
            lines.append(
                f"- [{text}]({t['url']}) "
                f"（{t['like_count']}❤ {t['retweet_count']}↺ {t['view_count']}👁）"
            )
        lines.append("")

    return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log("=== Twitter daily fetch started ===")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)
    today  = datetime.now().strftime("%Y-%m-%d")

    out_dir = TWEETS_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = init_db()
    all_new = []
    errors  = []

    for i, handle in enumerate(HANDLES):
        log(f"[{i+1}/{len(HANDLES)}] Fetching @{handle} ...")
        tweets = fetch_user_tweets(handle, cutoff)

        new_count = 0
        for t in tweets:
            if not is_seen(conn, t["id"]):
                mark_seen(conn, t["id"], handle)
                all_new.append(t)
                new_count += 1

        log(f"  -> {len(tweets)} recent, {new_count} new")
        if len(tweets) == 0:
            errors.append(handle)

    conn.commit()
    conn.close()

    # Save JSON
    out_json = out_dir / "tweets.json"
    with open(out_json, "w") as f:
        json.dump({
            "date":              today,
            "cutoff_hours":      CUTOFF_HOURS,
            "total_new":         len(all_new),
            "accounts_fetched":   len(HANDLES) - len(errors),
            "errors":            errors,
            "tweets":            all_new,
        }, f, ensure_ascii=False, indent=2)

    # Save Markdown
    out_md = out_dir / "tweets.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(tweets_to_markdown(all_new))

    log(f"=== Done: {len(all_new)} new tweets -> {out_json} + {out_md} ===")

    print(f"NEW_TWEETS={len(all_new)}")
    print(f"OUTPUT_JSON={out_json}")
    print(f"OUTPUT_MD={out_md}")

if __name__ == "__main__":
    main()
