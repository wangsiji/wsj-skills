---
name: wsj-card-visual
description: 生成图形知识卡片：当用户要求"图形知识卡片""知识可视化卡片"时，从铸卡/素材/笔记生成高密度 HTML 卡片（Kindle 纸书风/现代轻暖风/Apple 极简/深色信息长图四种预设），纯 HTML 单文件浏览器直接预览。
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [knowledge-card, visual, card-generation, html]
    category: creative
---

# 图形知识卡片生成（路由版 v2）

> 主文件只做路由 + 风格决策 + 检查。每种风格的 CSS/色值/布局在 `references/`，按需读取。

## 黄金 5 条

1. 内容决定形式，不锁死模板
2. 单文件 HTML 输出，零依赖，浏览器直接预览
3. 风格由用户暗示匹配（不提→默认 Kindle 纸书风）
4. 风格冲突时：用户明说 > 内容类型匹配 > 默认 A
5. 风格切换时不重新构建整个卡片，只替换 CSS 变量

## Rule Priority（风格决策）

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P1** | 用户明确指定 | "苹果风""深色"→直接对应风格 |
| **P2** | 内容类型匹配 | 深度文→纸书；自媒体→轻暖；教程→深色长图；工具→极简 |
| **P3** | 风格关键词暗示 | "Notion风""公众号""飞书"→映射对应风格 |
| **P4** | 默认 | 不提→A (Kindle 纸书风) |

## Task Router

```
用户请求（"生成知识卡片"/"图形化"/"做成卡片"）
  ↓
Step 1: 分析输入来源（铸卡/素材/笔记全文）
Step 2: 风格决策（P1~P4 → 读对应 style-*.md）
Step 3: 构建 HTML（cardData 规范 → references/cardData.md）
Step 4: 生成 → 写入临时文件 → 部署到公开目录
Step 5: 质量检查（validate.html）
```

## 风格决策对照表

| 用户说 | 风格 |
|--------|------|
| 不提 | A (Kindle 纸书风) |
| "苹果风""Notion风""Linear风""极简""公众号" | D (Apple 极简白) |
| "信息图""长图""教程" | C (深色信息长图) |
| "暖色""轻阅读" | B (现代轻暖风) |
| "学术""知识卡" | D 变体 (学术知识卡配色) |

## 输入输出协议

**输入**：卡片文本/结构化数据 / 知识卡片名称
**输出**：单文件 HTML（`sudo cp` 到公开目录，终端预览）

## Pre-flight Check

- [ ] 输入类型已确认（铸卡/素材/笔记）
- [ ] 风格已定（A/B/C/D/变体）
- [ ] cardData 规范匹配（references/cardData.md）

## Post Check

- [ ] HTML 无外部依赖（纯内联/单文件）
- [ ] 所有卡片在浏览器可预览
- [ ] 公开目录部署成功
- [ ] 无漏的风格切换残留 CSS

## Never Do

- ❌ 多文件输出（只生成一个 HTML）
- ❌ 风格切换时重写整个卡片 CSS（只换变量）
- ❌ 直接输出到公开目录而不先本地验证
- ❌ 提风格时猜用户意图（不确定→确认再定）

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/style-guide.md` | 4 种风格色值/布局/内容适配规则全集 |
| `references/cardData.md` | cardData 字段规范（输入格式） |
| `references/deployment.md` | 部署方法（终端预览 + 公开目录） |
| `references/pitfalls.md` | 布局迭代教训 |
