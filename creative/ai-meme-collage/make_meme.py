#!/usr/bin/env python3
"""Render a bell_curve + center_wojak AI-coding-agent meme poster."""

from PIL import Image, ImageDraw, ImageFont
import math
import os
import random

OUTPUT = os.path.expanduser("~/ai_meme_collage.png")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

W, H = 1200, 900
BG = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
BLUE = (70, 130, 200)
GRAY = (180, 180, 180)
LTBLUE = (220, 235, 250)

# ── layout bounds ──
BELL_CENTER = W // 2
BELL_BOTTOM = H - 50
BELL_HEIGHT = 200  # peak height from baseline
BELL_WIDTH = 500   # 2 sigma spans this

CAPTION_Y0 = 40   # top of composition area (below bell starts at ~660)
CONTENT_TOP = 40
CONTENT_BOTTOM = H - 250  # bell-curve region starts here


def draw_bell_curve(draw):
    """Draw a bell-curve / IQ distribution chart at the bottom."""
    cx, bottom = BELL_CENTER, BELL_BOTTOM
    # light blue fill
    pts = [(cx - BELL_WIDTH, bottom)]
    for x_px in range(cx - BELL_WIDTH, cx + BELL_WIDTH + 1):
        t = (x_px - cx) / (BELL_WIDTH / 2.2)
        y = bottom - BELL_HEIGHT * math.exp(-t * t / 2)
        pts.append((x_px, y))
    pts.append((cx + BELL_WIDTH, bottom))
    draw.polygon(pts, fill=LTBLUE, outline=None)

    # left / right tail arrows
    for side, label, x_ofs in [(-1, "low IQ", -30), (1, "high IQ", 15)]:
        lx = cx + side * (BELL_WIDTH + 40)
        draw.text((lx - 30, bottom - 20), label, fill=GRAY, font=ImageFont.truetype(FONT_REG, 16))

    # axis labels
    draw.text((cx - 8, bottom + 8), "IQ", fill=BLACK, font=ImageFont.truetype(FONT_REG, 14))

    # red annotation zone labels on bell
    # left tail (below average)
    draw.text((cx - 200, bottom - BELL_HEIGHT - 30), "use tools", fill=RED, font=ImageFont.truetype(FONT_BOLD, 14))
    draw.text((cx + 120, bottom - BELL_HEIGHT - 30), "not AGI", fill=RED, font=ImageFont.truetype(FONT_BOLD, 14))
    draw.text((cx - 220, bottom - BELL_HEIGHT + 10), "'just autocomplete'", fill=RED, font=ImageFont.truetype(FONT_REG, 12))
    draw.text((cx + 140, bottom - BELL_HEIGHT + 10), "'merge my PR'", fill=RED, font=ImageFont.truetype(FONT_REG, 12))


def draw_wojak_face(draw, cx, cy, scale=1.0):
    """Draw a simple crying wojak / doomer face."""
    s = scale * 0.9
    # head oval
    r = 60 * s
    draw.ellipse([cx - r, cy - r * 1.2, cx + r, cy + r * 1.0], outline=BLACK, width=3, fill=(245, 245, 240))
    # eyes
    eye_y = cy - 15 * s
    eye_w, eye_h = 10 * s, 6 * s
    draw.ellipse([cx - 25 * s - eye_w, eye_y - eye_h, cx - 25 * s + eye_w, eye_y + eye_h], fill=BLACK)
    draw.ellipse([cx + 25 * s - eye_w, eye_y - eye_h, cx + 25 * s + eye_w, eye_y + eye_h], fill=BLACK)
    # tear drops
    for t_x in [cx - 25 * s, cx + 25 * s]:
        draw.ellipse([t_x - 3, eye_y + 10, t_x + 3, eye_y + 22], fill=(100, 180, 255))
        draw.ellipse([t_x - 2, eye_y + 18, t_x + 2, eye_y + 28], fill=(100, 180, 255))
    # sad mouth
    draw.arc([cx - 20 * s, cy + 10 * s, cx + 20 * s, cy + 35 * s], 0, 180, fill=BLACK, width=2)
    # eyebrows (angled down for sad look)
    draw.line([cx - 40 * s, eye_y - 20 * s, cx - 18 * s, eye_y - 15 * s], fill=BLACK, width=3)
    draw.line([cx + 40 * s, eye_y - 20 * s, cx + 18 * s, eye_y - 15 * s], fill=BLACK, width=3)


def draw_text(draw, text, x, y, font_size, color=BLACK, font_bold=True, rotation=0, anchor="lt"):
    """Draw text, optionally rotated."""
    fp = FONT_BOLD if font_bold else FONT_REG
    font = ImageFont.truetype(fp, font_size)
    # For simplicity draw rotated with ImageDraw.text + anchor
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Draw at position; rotation is simplified
    draw.text((x, y), text, fill=color, font=font)
    return tw, th


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Background chaos: faint grid ──
    for gx in range(0, W, 80):
        draw.line([(gx, 0), (gx, H - 250)], fill=(245, 245, 245), width=1)
    for gy in range(0, H - 250, 80):
        draw.line([(0, gy), (W, gy)], fill=(245, 245, 245), width=1)

    # ── Captions ──
    # TITLE (top-left)
    draw_text(draw, "PAUSE AI", 40, 45, 50, BLACK, True)
    draw_text(draw, "OR ELSE", 42, 98, 44, RED, True)

    # BIG slogans
    draw_text(draw, "Hehe coding agents go brrrrr", 320, 50, 36, BLACK, True)
    draw_text(draw, "周限额已重置！！", 390, 100, 32, BLACK, True)

    # MEDIUM claims
    mid_y = 160
    claims = [
        ("It used tools so it doesn't count", 40, 24),
        ("This proves I was right all along", 40, 148),
        ("Only 2% understand 😎", 620, 200, 26),
        ("合并我的 PR", 620, 240, 26),
    ]
    for c in claims:
        txt, x, y = c[0], c[1], c[2]
        fs = c[3] if len(c) > 3 else 24
        draw_text(draw, txt, x, y, fs, BLACK, True)

    # SMALL labels (scattered)
    smalls = [
        ("not a bubble", 110, 300, 18, GRAY),
        ("infrastructure", 280, 310, 16, GRAY),
        ("trust me bro", 550, 330, 18, GRAY),
        ("autocomplete+", 780, 320, 16, GRAY),
        ("liquid-cooled cope", 850, 280, 16, GRAY),
        ("~2025 colorized", 440, 360, 14, GRAY),
        ("we reset your limits", 710, 370, 16, GRAY),
        ("AGI next tuesday", 950, 340, 16, GRAY),
        ("Vibe coding era", 160, 370, 18, GRAY),
    ]
    for txt, x, y, fs, col in smalls:
        draw_text(draw, txt, x, y, fs, col, False)

    # SPAM (repeated background text)
    spam_phrases = ["we reset your weekly limits", "go brrrrr", "not financial advice", "trust the process"]
    for i, phrase in enumerate(spam_phrases):
        sx = 30 + i * 280
        sy = 430 + (i % 2) * 30
        draw_text(draw, phrase, sx, sy, 14, (200, 200, 200), False)

    # ── Wojak face center ──
    draw_wojak_face(draw, W // 2, 250, scale=1.8)

    # Extra small wojak right side (soyjak)
    draw_wojak_face(draw, 950, 180, scale=0.6)

    # ── Bell curve ──
    draw_bell_curve(draw)

    # ── Speech bubble from wojak ──
    bubble_text = "They're using tools...\nthat doesn't count!!"
    for li, line in enumerate(bubble_text.split("\n")):
        draw_text(draw, line, W // 2 - 100, 175 + li * 22, 16, BLACK, True)

    # ── Bottom line ──
    draw_text(draw, "AI MEME COLLAGE · 2025", W // 2 - 130, H - 30, 20, GRAY, False)

    img.save(OUTPUT)
    print(f"Saved → {OUTPUT}")
    print(f"Size: {W}x{H}")


if __name__ == "__main__":
    main()
