---
name: wsj-clip
description: 统一剪藏：当用户发来链接或要求保存/收藏/总结网页、公众号、X、B站、播客内容时，抓取并用 AI 总结，按来源分类归档到 Obsidian 的 00-LLM-WiKi/Raw/。用户说"剪藏""clip""保存这篇文章""帮我记录一下"时使用。
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [clipping, web-clipper, xiaoyuzhou, bilibili, getnote]
    category: productivity
---

# Clip — 统一剪藏（路由版 v2）

> 主文件只做路由 + 最高优先级规则。细节在 `references/`，按需读取。

## 黄金 5 条

1. 采集前先查重，命中已知信源→跳过/转消化（不重复灌）
2. 磁盘真值 > 索引数字（`ls Raw/ | wc -l` 而非 Active.md 统计）
3. 原文抓取 + AI 总结**并行**启动，合并输出
4. 来源信任层级必写（可信度判断固定惯例）
5. 数据完整 > 内容美化；批量写前重测 vault 状态

## Rule Priority（冲突时听谁）

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | 数据完整 | 不删用户已有内容；git 脏状态不 commit（除非许可） |
| **P1** | 去重纪律 | 已知信源不重复灌入（建得起清得掉） |
| **P2** | 来源信任 | 不同来源按信任层级标注，不自作主张升信任 |
| **P3** | 格式规范 | frontmatter / 文件名 / 合并格式 |
| **P4** | 效率 | 并行、批量、降级策略 |

## Task Router

```
用户给链接 / "剪藏" / "保存"
  ↓ 识别来源
  A 网页/公众号 → references/workflow-web.md
  B X/Twitter   → references/workflow-web.md (vnc-clip.py)
  C GitHub      → references/workflow-web.md (raw README)
  D B站/视频号   → references/workflow-media.md (getnote)
  E 小宇宙播客   → references/workflow-media.md (getnote+show notes)
  F 批量(N链接)  → 并行提交，不串行
  ↓
并行：步骤A原文抓取 ─┐
                       ├→ merge-clip.py → Raw/
步骤B getnote AI总结 ─┘
  ↓
质量检查 → 通知用户
```

## 输入输出协议

**输入**：URL + 类型（自动识别）+ 是否批量
**输出**：`00-LLM-WiKi/Raw/{来源}_{作者}_{标题}.md`，含 frontmatter + 原文 + `## AI 智能总结`

## Pre-flight Check

- [ ] vault 状态已重测（非过期索引）
- [ ] URL 未在 Raw/ 重复（查重闸门）
- [ ] 来源类型已识别

## Post Check

- [ ] 文件存在、frontmatter 完整、内容非空
- [ ] 无重复 H2 标题（merge 坑）
- [ ] 来源信任层级已写
- [ ] git 状态未盲目 commit

## Never Do

- ❌ 盲信 Active.md 统计数字（用 `ls Raw/` 真值）
- ❌ 重复灌入已知信源
- ❌ git 脏状态 `git commit`（除非用户许可）
- ❌ 串行处理批量链接（应并行）
- ❌ 全文存 manpage 型 README（>30KB 节选）

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/workflow-web.md` | 网页/公众号/X/GitHub 剪藏流程 |
| `references/workflow-media.md` | B站/视频号/小宇宙媒体剪藏 |
| `references/getnote-api.md` | getnote AI 总结 API 规则 |
| `references/dedup-gate.md` | 批量写前 vault 校验 + 查重 |
| `references/merge-clip-pitfalls.md` | merge-clip.py 调用坑 |
| `references/note-attribute-format.md` | 笔记属性格式标准 |
| `references/troubleshooting.md` | 排错表 |
| `references/wechat-article-extraction.md` | 公众号提取 |
| `references/x-article-clipping.md` | X 文章剪藏 |
| `references/xiaoyuzhou-podcast-clipping.md` | 小宇宙播客 |
| `references/image-article-handling.md` | 图片型公众号处理 |
| `references/bilibili-api-fallback.md` | B站 API 备用 |

## 产出管线

```
采集 → 00-LLM-WiKi/Raw/ → 精选 → Topics/(常青) → Outputs/(创作)
```
