---
name: kcv-pitfalls
description: 图形卡片布局迭代教训 + 参考图调整流程。
---

## Pitfalls（布局迭代教训）

- **不要大改整体风格**：用户说「改的不好」→ 立即回滚到上一版，逐项追问具体哪里不对
- **紧凑化**：用户说「内容紧凑点」→ 缩小 padding/margin/font-size，保持结构和配色不变
- **左右布局**：用户要求左右分布 → 用 CSS grid 显式控制列宽（不等宽，内容多的列更宽），不用 flex-wrap 自动折行 — flex-wrap 在窄屏会变回纵向
- **一屏完整显示**：用户要求「一屏看完」→ 压缩所有间距，缩至最小可读字号（7-11px），900px 高内完整容纳所有区块
- **中文文字渲染**：知识卡片中大量中文文字时，AI 生图模型（混元/FLUX/Midjourney）不能准确渲染中文。优先用 HTML/CSS 方式生成后截屏。如果用户要求用 AI 生图，告知局限：中文会乱码/缺笔画，结构化排版无法保证。需要中文文字+生图效果时，推荐 Lovart GPT Image 2（中文渲染较好但仍有漂移）或直接用 HTML 截屏。
- **CloudBase 混元生图水印**：混元生图会在右下角加「AI生成」水印。prompt 中加「不要文字，不要水印」不一定能去掉。如需去除，用 Python 裁剪底部或告知用户此局限。
- **Lovart GPT Image 2 调用**：Lovart 的 GPT Image 2 中文文字渲染能力优于传统文生图模型。调用：`python3 ~/.hermes/skills/lovart-skill/agent_skill.py chat --prompt \"...\" --prefer-models '{\"IMAGE\":[\"generate_image_gpt_image_2\"]}' --json --download`。先 `config --json` 再 `chat`。详见 `references/image-gen-chinese-text.md`。

## 参考图调整流程

当用户发参考图并说「做成这样的」时：

1. **先试 vision** — `browser_navigate(file://...路径)` → `browser_vision` 分析配色/布局/字体/间距
2. **vision 不可用时** — 直接告诉用户看不到图，请他们描述具体要改什么（配色/字体/布局/间距/哪个区不对）。**不要**用 ImageMagick 像素采样自行推断并重写整体风格（实践证明会产生用户不接受的版本）。
3. **迭代原则**：
   - 每次只改用户指出的具体问题，不要大改整体风格
   - 改完展示截图，等反馈再继续
   - 用户说「改的不好」→ 立即回滚到上一版，问具体哪里不对
   - 用户说「要和他相似一点」→ 逐项追问：颜色像不像？字体像不像？间距像不像？布局结构像不像？
4. **风格切换规则**：
   - 用户不发参考图 → 默认风格 A（Kindle 纸书）
   - 用户发参考图说「做成这样的」→ 按用户要求的方向做
   - 用户对某一版说「回到刚才那一版」→ 立即恢复上一版本，不要争论
