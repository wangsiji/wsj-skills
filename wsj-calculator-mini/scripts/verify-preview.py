#!/usr/bin/env python3
"""verify-preview.py — 检查 preview.html 的关键视觉元素是否可见

用法:
    python3 verify-preview.py [--url http://192.3.16.123/preview.html]

依赖: Pillow (pip install Pillow)
"""
import subprocess
import sys
import os
from PIL import Image

SHOT_PATH = "/tmp/shot_verify.png"

def capture(url: str, width=390, height=844) -> Image.Image | None:
    cmd = [
        "chromium", "--headless", "--disable-gpu",
        f"--screenshot={SHOT_PATH}",
        f"--window-size={width},{height}",
        url
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"chromium error: {r.stderr}", file=sys.stderr)
        return None
    try:
        return Image.open(SHOT_PATH)
    except FileNotFoundError:
        print(f"Screenshot not found: {SHOT_PATH}", file=sys.stderr)
        return None

def check_tab_bar(img: Image.Image) -> bool:
    """Tab bar 应该占据底部 ~80px，且有实际内容渲染（非纯色背景）

    ⚠️ 旧版检查 avg > 15 不充分（背景过渡行就能通过）。
    正确检查：底部 80px 区域应该有 > 0.5% 的暗色像素（文字内容）。
    """
    import numpy as np
    w, h = img.size
    arr = np.array(img)

    # 检查 tab bar 区域（底部 80px）是否有暗色像素（文字内容）
    tab = arr[h-80:]
    dark_pixels = (tab < 200).sum()
    total_channels = tab.shape[0] * tab.shape[1]
    dark_ratio = dark_pixels / (total_channels * 3)  # 三通道

    print(f"  Tab bar dark pixel ratio: {dark_ratio:.2%} (need > 0.5%)")
    return dark_ratio > 0.5

def check_content(img: Image.Image) -> bool:
    """内容区（前 80% 高度）应该有足够多非背景像素"""
    w, h = img.size
    content_rows = sum(
        1 for y in range(0, int(h * 0.8))
        for x in range(0, w, 4)
        if sum(img.getpixel((x, y))) / 3 > 20
    )
    return content_rows > 1000

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://192.3.16.123/preview.html"

    print(f"Capturing: {url}")
    img = capture(url)
    if img is None:
        sys.exit(1)

    w, h = img.size
    print(f"Screenshot size: {w}x{h}")

    tab_ok = check_tab_bar(img)
    content_ok = check_content(img)

    print(f"Tab bar visible: {tab_ok}")
    print(f"Content area ok: {content_ok}")

    if not tab_ok:
        print("\n⚠️  WARNING: Tab bar not visible in screenshot!")
        print("Likely cause: emoji icons are black/transparent in headless Chromium,")
        print("or tab-bar background too dark to contrast with body background.")
        print("Fix: use white tab-bar background + colored SVG/text icons.")
        sys.exit(1)
    if not content_ok:
        print("\n⚠️  WARNING: Content area appears empty!")
        sys.exit(1)

    print("\n✅ All checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
