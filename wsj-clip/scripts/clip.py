#!/usr/bin/env python3
"""
Obsidian Web Clipper - Headless Script (方案B)
使用 Chrome headless + bs4 + markdownify 提取网页内容并保存到 Obsidian vault

Usage:
  python3 clip.py <url> [--vault VAULT_PATH]

Examples:
  python3 clip.py https://example.com/article
  python3 clip.py https://example.com/article --vault /home/wangsiji/projects/wsj-second-brain
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as md


VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "/home/wangsiji/projects/wsj-second-brain")
CLIP_DIR = os.environ.get("CLIP_DIR", "00-LLM-WiKi/Raw")
CHROME = "/usr/bin/google-chrome-stable"


def fetch_rendered_html(url: str, timeout: int = 30) -> str:
    """Use Chrome headless to get fully rendered DOM"""
    result = subprocess.run(
        [CHROME, "--headless", "--dump-dom", "--no-sandbox", url],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"Chrome failed: {result.stderr}")
    return result.stdout


def extract_article(html: str, url: str) -> dict:
    """Extract article content using bs4 heuristics"""
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "noscript", "iframe", "form", "svg", "canvas"]):
        tag.decompose()

    # Try to get title
    title = ""
    for sel in ["h1", "title", "meta[property='og:title']", "meta[name='title']"]:
        el = soup.select_one(sel)
        if el:
            if el.name == "meta":
                title = el.get("content", "")
            else:
                title = el.get_text(strip=True)
            break

    # Try to get author
    author = ""
    for sel in ["meta[name='author']", "meta[property='article:author']",
                ".author", '[rel="author"]']:
        el = soup.select_one(sel)
        if el:
            if el.name == "meta":
                author = el.get("content", "")
            else:
                author = el.get_text(strip=True)
            break

    # Try to get description
    description = ""
    for sel in ["meta[name='description']", "meta[property='og:description']"]:
        el = soup.select_one(sel)
        if el:
            description = el.get("content", "")
            break

    # Try to find main content area (heuristic)
    content_candidates = [
        soup.select_one("article"),
        soup.select_one("[role='main']"),
        soup.select_one("main"),
        soup.select_one(".post-content, .article-content, .entry-content, .content"),
        soup.select_one("#content, #main-content, #article"),
        soup.select_one(".post, .article, .entry"),
    ]
    content_el = next((c for c in content_candidates if c), soup.body)

    # Try to get the page title from <h1> inside main content
    if not title:
        h1 = content_el.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    # Convert to markdown
    content_html = str(content_el)
    markdown = md(content_html, heading_style="ATX", strip=["a"])

    # Clean up excessive whitespace
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    domain = urlparse(url).netloc

    return {
        "title": title or domain,
        "author": author,
        "description": description,
        "content": markdown,
        "domain": domain,
        "url": url,
    }


def make_filename(title: str, url: str) -> str:
    """Create safe filename from title"""
    name = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]
    name = re.sub(r'\s+', '_', name.strip())
    if not name:
        name = urlparse(url).netloc.replace(".", "_")
    return f"{name}.md"


def format_note(result: dict) -> str:
    """Format as Obsidian markdown with frontmatter"""
    today = date.today().isoformat()
    frontmatter = {
        "title": result["title"],
        "source": result["url"],
        "domain": result["domain"],
        "clipped": today,
    }
    if result["author"]:
        frontmatter["author"] = result["author"]
    if result["description"]:
        frontmatter["description"] = result["description"]

    fm_lines = ["---"]
    for k, v in frontmatter.items():
        fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")

    return "\n".join(fm_lines) + "\n\n" + result["content"]


def main():
    parser = argparse.ArgumentParser(description="Clip web page to Obsidian vault")
    parser.add_argument("url", help="URL to clip")
    parser.add_argument("--vault", default=VAULT, help=f"Obsidian vault path (default: {VAULT})")
    parser.add_argument("--dir", default=CLIP_DIR, help=f"Subdirectory in vault (default: {CLIP_DIR})")
    parser.add_argument("--output", "-o", help="Output file path (overrides vault/dir)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of saving")
    args = parser.parse_args()

    print(f"\U0001f50d Fetching: {args.url}", file=sys.stderr)
    html = fetch_rendered_html(args.url)

    print(f"\U0001f4c4 Extracting content...", file=sys.stderr)
    result = extract_article(html, args.url)

    note = format_note(result)

    if args.stdout:
        print(note)
        return

    if args.output:
        path = Path(args.output)
    else:
        vault = Path(args.vault)
        clip_dir = vault / args.dir
        clip_dir.mkdir(parents=True, exist_ok=True)
        filename = make_filename(result["title"], args.url)
        path = clip_dir / filename

    path.write_text(note)
    print(f"\u2705 Saved: {path}", file=sys.stderr)
    print(f"   Title: {result['title']}")
    print(f"   Content: {len(result['content'])} chars")


if __name__ == "__main__":
    main()
