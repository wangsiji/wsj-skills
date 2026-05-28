#!/usr/bin/env python3
"""Generate static timeline website from info-feed data.

Reads recaller items, renders HTML template, syncs to nginx serve dir.

Usage:
    cd ~/projects/aihot-local && python3 generate.py

Output:
    - output/index.html (local backup)
    - rsync'd to /var/www/info-feed/ (nginx serve path)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add info-feed project to path
INFO_FEED_DIR = os.path.expanduser("~/projects/info-feed")
sys.path.insert(0, INFO_FEED_DIR)
os.chdir(INFO_FEED_DIR)

# Config
OUTPUT_DIR = os.path.expanduser("~/projects/aihot-local/output")
TEMPLATE_FILE = os.path.expanduser("~/projects/aihot-local/templates/index.html")
NGINX_SERVE_DIR = "/var/www/info-feed/"
BJT = timezone(timedelta(hours=8))

# Content type display
TYPE_LABELS = {
    "twitter": ("twitter", "Twitter"),
    "longform": ("longform", "长文"),
    "podcast": ("podcast", "播客"),
    "video": ("video", "视频"),
}


def load_items():
    """Load items from feed system's data."""
    # Import the feed system's data collection
    try:
        from feed import collect_all_items
        all_items = collect_all_items()
    except ImportError:
        # Fallback: find and read cached data
        items = []
        cache_dir = os.path.join(INFO_FEED_DIR, "data")
        if os.path.exists(cache_dir):
            for fname in sorted(os.listdir(cache_dir)):
                if fname.endswith(".json"):
                    with open(os.path.join(cache_dir, fname)) as f:
                        items.extend(json.load(f))
        all_items = items

    # Sort by time descending
    all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_items[:100]  # Top 100


def format_item_html(item):
    """Render a single item as HTML card."""
    content_type = item.get("content_type", "short")
    type_key, type_label = TYPE_LABELS.get(content_type, ("default", content_type))

    title = item.get("title", "").strip() or "无标题"
    url = item.get("url", "#")
    author = item.get("author", "")
    source = item.get("source", "")
    content = item.get("content", "")

    # Preview: first 200 chars
    preview = content[:200].strip()
    if len(content) > 200:
        preview += "..."

    # Format timestamp
    created = item.get("created_at", "")
    time_str = ""
    if created:
        try:
            if isinstance(created, str):
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            else:
                dt = created
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            time_str = dt.astimezone(BJT).strftime("%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = str(created)

    return f'''<div class="item" data-type="{type_key}">
  <div class="item-meta">
    <span class="tag tag-{type_key}">{type_label}</span>
    <span>{author}</span>
  </div>
  <div class="item-title"><a href="{url}" target="_blank">{_escape(title)}</a></div>
  <div class="item-content">{_escape(preview)}</div>
  <div class="item-footer">
    <span class="item-author">{_escape(author)}</span>
    <span class="item-time">{time_str}</span>
  </div>
</div>'''


def _escape(s):
    """Basic HTML escaping."""
    s = str(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("\"", "&quot;").replace("'", "&#39;")
    return s


def generate():
    """Generate the static site."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    items = load_items()
    print(f"Loaded {len(items)} items")

    if not items:
        items_html = '<div class="empty"><div>暂无内容</div><div class="empty-sub">数据收集完成后自动更新</div></div>'
    else:
        items_html = "\n".join(format_item_html(item) for item in items)

    # Read template and substitute
    with open(TEMPLATE_FILE) as f:
        template = f.read()

    html = template.replace("<!-- ITEMS_PLACEHOLDER -->", items_html)

    # Write output
    output_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written to {output_path}")

    # Rsync to nginx
    cmd = ["rsync", "-a", "--delete", OUTPUT_DIR + "/", NGINX_SERVE_DIR]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Synced to {NGINX_SERVE_DIR}")
    else:
        print(f"rsync error: {result.stderr}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(generate())
