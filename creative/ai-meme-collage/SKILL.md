---
name: ai-meme-collage
description: "Create dense AI/crypto/Twitter-style meme collage images with white-background wojak brainrot, bell-curve/IQ-distribution charts, chaotic captions, founder/investor caricature jokes, and terminally-online narrative maps. Use when the user asks for meme 梗图, wojak collage, brainrot meme, AI/crypto meme poster, 类似 Sloptember / hehe data center stocks go brrrr style images, or wants prompt + generation workflow for high-density meme images."
---

# AI Meme Collage

## What this skill makes

High-density meme posters similar to AI/crypto Twitter collage images:

- white canvas, chaotic but readable layout
- bold black Arial/Impact-style captions
- wojak / soyjak / npc / hooded-doomer / tech-founder caricatures
- bell curve / IQ distribution / chart background
- repeated ironic slogans, short accusations, overconfident claims
- intentionally low-polish screenshot/copy-paste aesthetic
- “online discourse compressed into one image” feeling

Avoid copying a real person's exact likeness unless the user explicitly provides permission or asks for public-figure parody. Prefer archetypes: “VC wojak”, “AI founder wojak”, “security doomer”, “crypto degen”, “researcher NPC”.

## Quick workflow

1. **Extract theme**
   - Topic: AI agents, crypto token, data centers, startup drama, LLM coding, VC takes, etc.
   - Target: who is being mocked / celebrated?
   - Core joke: one sentence.
   - Tone: bullish, bearish, absurdist, satirical, schizo-wall, or propaganda.

2. **Write 10–18 caption fragments**
   Mix these types:
   - Big slogan: 3–8 words, all caps or title case.
   - Bad take: fake confident sentence.
   - Cope line: “This proves I was right all along”.
   - Bullish line: “go brrrrr”, “number up”, “merge my PR”.
   - Degen line: “only 2% understand”, “not financial advice”.
   - Tiny background text: repeated phrase, label, fake quote.

3. **Choose layout**
   - `bell_curve`: IQ distribution / adoption curve at bottom or center.
   - `whiteboard_chaos`: scattered text and faces on white background.
   - `two_tribes`: left/right camps arguing.
   - `center_wojak`: one huge crying wojak or doomer in center.
   - `market_map`: meme characters arranged by conviction / intelligence / liquidity.

4. **Generate image with a style prompt**
   Use image generation for the base collage. Ask for mostly readable text, but expect some text artifacts. If exact text matters, generate the image with empty speech/text areas and add final captions afterward in an editor/PIL/Canva.

5. **Post-process if needed**
   For exact wording: overlay text manually using black bold Arial/Helvetica/Impact, irregular sizes, slight rotations, and dense spacing.

## Prompt template

```text
Create a chaotic high-density internet meme collage poster on a clean white background, absurd AI/crypto Twitter brainrot style.

Theme: {theme}
Core joke: {core_joke}
Mood: {tone}

Composition:
- ultra-wide poster, many scattered meme characters and captions
- bottom/center has a light-blue bell curve / IQ distribution chart with red axis labels
- large crying wojak face near center
- several black-and-white wojak / soyjak / npc / hooded doomer / tech founder caricatures pasted around the canvas
- a few tiny fake screenshots and chart snippets
- deliberately copy-pasted, low-polish, terminally-online meme aesthetic
- mostly white negative space but packed with jokes

Text style:
- bold black Arial / Impact captions, mixed sizes
- some all caps, some small paragraphs, some rotated labels
- keep the following captions readable where possible:
{caption_list}

Visual constraints:
- flat 2D meme collage, not polished illustration
- no cinematic lighting, no glossy 3D, no realistic photography
- rough hand-drawn line art, cropped PNG sticker feeling
- satirical, chaotic, funny, legible
```

## Caption recipe

For one image, produce:

- 1 title, upper-left or top-center
- 2 huge slogans, 48–96 px equivalent
- 4 medium claims, 24–40 px equivalent
- 6–10 tiny labels / fake quotes
- 2 repeated phrases for background spam

Example caption set:

```text
TITLE: PAUSE AI OR ELSE
BIG: Hehe data center stocks go brrrrr
BIG: The agents are coming
MEDIUM: It used tools so it doesn't count
MEDIUM: We reset your weekly limits
MEDIUM: Merge my pull request
MEDIUM: This is exactly what my 1998 paper predicted
SMALL: only 2% understand
SMALL: highly sophisticated autocomplete
SMALL: liquidity is a national security threat
SPAM: we reset your weekly limits
SPAM: not a bubble if the servers are warm
```

## Chinese meme variant

For 中文梗图, keep short punchy bilingual fragments because image models often render Chinese poorly. Best practice:

1. Generate background and characters with English placeholder text.
2. Overlay Chinese captions after generation.

Chinese caption style:

```text
暂停 AI 不然怎样
算力喝水了！！
这不是泡沫，这是基础设施
合并我的 PR
周限额已重置
只有 2% 的人懂
数据中心股票 go brrrrr
```

## Quality checklist

Before sending final image/prompt:

- [ ] It has one instantly readable main joke.
- [ ] It has 10+ micro-jokes for zoom-in payoff.
- [ ] Layout is intentionally chaotic but not blank.
- [ ] Text is bold, black, and high contrast.
- [ ] Characters are sticker-like, not polished portraits.
- [ ] If exact text matters, mention that final text overlay may be needed.

## Fast user intake

If the user only says “帮我做类似的”, use defaults:

- topic: current AI agents / coding agents discourse
- tone: absurdist bullish-bearish mixed satire
- layout: bell_curve + center_wojak
- ratio: landscape / ultra-wide
- language: bilingual, mostly English with a few Chinese punchlines

Ask only if the missing topic materially changes the joke.
