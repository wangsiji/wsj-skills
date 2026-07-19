#!/usr/bin/env python3
"""
Unified merge script for all clip outputs.

Usage:
    python3 scripts/merge-clip.py <source_type> <title> <author> <url> <body_file> <ai_summary_file>

    source_type: gzh | x | web | github | bilibili | xiaoyuzhou | channels | douyin
    ai_summary_file: path to AI summary text
    body_file: path to body/original content text

Output:
    00-LLM-WiKi/Raw/{source}_{author}_{title}.md
"""

import sys, re, os
from datetime import date

SOURCE_CONFIG = {
    "gzh":       {"platform": "GZH",   "tag": "公众号",   "category": "GZH"},
    "x":         {"platform": "X",      "tag": "Twitter",  "category": "X"},
    "web":       {"platform": "Web",    "tag": "网页",     "category": "Web"},
    "github":    {"platform": "GitHub", "tag": "GitHub",   "category": "GitHub"},
    "bilibili":  {"platform": "B站",    "tag": "B站",      "category": "B站"},
    "xiaoyuzhou":{"platform": "小宇宙", "tag": "小宇宙",    "category": "小宇宙"},
    "channels":  {"platform": "视频号", "tag": "视频号",   "category": "视频号"},
    "douyin":    {"platform": "DouYin", "tag": "抖音",     "category": "抖音"},
}

VAULT = "/home/wangsiji/projects/wsj-second-brain"


def merge(source_type: str, title: str, author: str, url: str,
          ai_summary: str, body: str) -> str:
    cfg = SOURCE_CONFIG.get(source_type)
    if not cfg:
        valid = ", ".join(SOURCE_CONFIG.keys())
        raise ValueError(f"Unknown source_type '{source_type}'. Valid: {valid}")

    now = date.today().strftime("%Y%m%d")

    frontmatter = f"""---
category:
  - "[[{cfg['category']}]]"
author:
  - "[[{author}]]"
url: "{url}"
tags: [剪藏, {cfg['tag']}]
created: {now}
modified: {now}
---

"""

    # Clean body (common cleanup)
    if body:
        body = re.sub(r'<video[^>]*>.*?</video>', '', body, flags=re.DOTALL)
        body = re.sub(r'^#js\\\\_row.+?^$\n', '', body, flags=re.MULTILINE | re.DOTALL)
        body = re.sub(r'^!\[cover_image\].+$\n?', '', body, flags=re.MULTILINE)
        body = re.sub(r'^原创.*$\n?', '', body, flags=re.MULTILINE)
        body = re.sub(r'在小说阅读器读本章\n去阅读\n在小说阅读器中沉浸阅读\n?', '', body)
        body = re.sub(r'往期回顾.*$', '', body, flags=re.DOTALL)
        body = body.strip()

    ai_section = f"## AI 智能总结\n\n{ai_summary.strip()}\n\n" if ai_summary else ""
    body_section = f"## 剪藏原文\n\n{body}\n" if body else ""

    merged = frontmatter + "# " + title + "\n\n" + ai_section + body_section

    # Output path: 00-LLM-WiKi/Raw/{source}_{author}_{title}.md
    output_dir = os.path.join(VAULT, "00-LLM-WiKi", "Raw")
    os.makedirs(output_dir, exist_ok=True)

    safe_title = re.sub(r'[\\/:*?"<>|]', '', title).replace('\n', ' ').strip()[:80]
    safe_title = re.sub(r'\s+', '_', safe_title)
    source_prefix = {
        "gzh": "公众号", "x": "X", "web": "Web", "github": "GitHub",
        "bilibili": "B站", "xiaoyuzhou": "小宇宙", "channels": "视频号", "douyin": "抖音",
    }[source_type]
    filename = f"{source_prefix}_{author}_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(merged)

    return filepath


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python3 merge-clip.py <type> <title> <author> <url> <body_file> <ai_summary_file>")
        sys.exit(1)

    source_type = sys.argv[1]
    title = sys.argv[2]
    author = sys.argv[3]
    url = sys.argv[4]

    with open(sys.argv[5]) as f:
        body = f.read()
    with open(sys.argv[6]) as f:
        ai_summary = f.read()

    filepath = merge(source_type, title, author, url, ai_summary, body)
    print(f"✅ {filepath}")
