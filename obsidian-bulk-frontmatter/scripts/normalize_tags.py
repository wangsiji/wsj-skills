#!/usr/bin/env python3
"""Bulk-normalize `tags:` across a folder of Obsidian notes.

Usage:
    python normalize_tags.py --dir /path/to/Evergreen \
        --namespace "心智模型/" --dry-run

What it does:
  - Reads every *.md note.
  - Parses `tags:` whether single-line ([a, b]) or multi-line (YAML sequence).
  - Strips leading '#', surrounding quotes, and whitespace from each item.
  - Keeps only items starting with --namespace (drops dirty/orphan tags).
  - Rewrites as a single-line `tags: [x, y, z]` list.
  - Self-verifies: prints any note whose tags line still violates the schema.

Run with --dry-run to preview changes without writing.
"""
import argparse
import os
import re
import sys

FRONTMATTER_RE = re.compile(r"^(---\n.*?\n---\n)", re.DOTALL)
TAGS_BLOCK_RE = re.compile(r"^tags:(\[.*?\]|\n(?:\s*-\s*.+\n)+)", re.MULTILINE | re.DOTALL)


def parse_items(block: str):
    block = block.strip()
    if block.startswith("["):
        raw = block.strip("[]")
        return [i.strip() for i in raw.split(",") if i.strip()]
    return [
        re.match(r"\s*-\s*(.+)$", ln).group(1).strip()
        for ln in block.split("\n")
        if ln.strip().startswith("-")
    ]


def normalize(items, namespace):
    out, dropped = [], []
    for it in items:
        cleaned = it.lstrip("#").strip().strip('"').strip("'").strip()
        if cleaned.startswith(namespace):
            out.append(cleaned)
        else:
            dropped.append(it)
    return out, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="notes folder")
    ap.add_argument("--namespace", default="心智模型/", help="keep only tags with this prefix")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    dropped_total = []
    offenders = []

    for fn in sorted(os.listdir(args.dir)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(args.dir, fn)
        with open(p, encoding="utf-8") as f:
            text = f.read()
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        fm = m.group(1)
        tb = TAGS_BLOCK_RE.search(fm)
        if not tb:
            continue
        items = parse_items(tb.group(1))
        out, dropped = normalize(items, args.namespace)
        dropped_total.extend((fn, d) for d in dropped)
        new_block = "[" + ", ".join(out) + "]"
        new_fm = fm[: tb.start()] + "tags: " + new_block + fm[tb.end():]
        if not re.match(r"^tags: \[(" + re.escape(args.namespace) + r"[^,\s]+(, )?)+\]$", new_fm, re.MULTILINE):
            offenders.append(fn)
        if not args.dry_run:
            with open(p, "w", encoding="utf-8") as f:
                f.write(text[: m.start(1)] + new_fm + text[m.end(1):])
        changed += 1
        print(f"[{'DRY' if args.dry_run else 'WRITE'}] {fn}: {new_block}")

    print(f"\nNotes touched: {changed}")
    print(f"Dropped dirty/orphan tags: {len(dropped_total)}")
    for fn, d in dropped_total:
        print(f"  {fn}: dropped {d!r}")
    if offenders:
        print(f"\nVERIFY FAILED for: {offenders}")
        sys.exit(1)
    print("VERIFY OK: all tags lines conform to schema.")


if __name__ == "__main__":
    main()
