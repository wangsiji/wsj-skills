---
name: wsj-knowledge-card
description: 将互联网知识经 AI 蒸馏成结构化常青卡片：当用户要求"做一张知识卡""整理成卡片""把概念写成常青卡片"时，输出 7 节结构（问题→概念→关系→案例→行动→边界→洞察），Insight 节留空由用户填。AI 提炼公共知识，人沉淀私人知识。
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [knowledge, card, second-brain, evergreen]
    category: knowledge
---

# Knowledge Card · 个人知识引擎（路由版 v2）

> 主文件只做路由 + 最高优先级规则。7 节格式模板 + 写作指南在 `references/`，按需读取。

## 黄金 5 条

1. AI 提炼公共知识，Insight 节留空由用户填（AI 不代劳认知）
2. 7 节固定结构：问题→概念→关系→案例→行动→边界→洞察
3. Frontmatter 仅 5 字段：name/description/category/tags/source/status
4. 每节独立发光，不用 `---` 分割线
5. 卡片文件名 = 核心词，不带 `# ` 标题行

## Rule Priority

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | Insight 留白 | 用户内化不可替，AI 只写到边界节 |
| **P1** | 7 节结构完整 | 缺任何一节需注明"暂缺"而非编造 |
| **P2** | 数据真实 | 来源/依据可追溯，不编造引用 |
| **P3** | 格式规范 | frontmatter / callout 映射 / H2 不重复 |

## Task Router

```
用户说"做一张卡片/整理成卡片"
  ↓
A 从剪藏素材生成 → 先读 clip 素材 → 接主流程
B 从已有笔记转化 → 提取核心概念 → 接主流程
C 从零生成标准卡片 → 直接走 7 节
  ↓
主流程：问题化 → 结构化(7节) → 关联化(backlinks) → 保存到 03-Resources/Evergreen/
  ↓
批量重写 → references/batch-rewrite.md
边界条件处理 → references/edge-cases.md
```

## 输入输出协议

**输入**：概念名 / 素材链接 / 笔记文本
**输出**：`03-Resources/Evergreen/{核心词}.md`（frontmatter + 7 节 H2 + callout 映射）

## Pre-flight Check

- [ ] 核心概念已确定（卡片文件名）
- [ ] 有真实素材/来源（非空想）
- [ ] category 归属（哪个 Area）

## Post Check

- [ ] 7 节全？Insight 留空？
- [ ] H2 无重复（批量重写后校验）
- [ ] frontmatter 5 字段完整
- [ ] callout 映射正确（!warning/!example/!check/!abstract）
- [ ] 来源可追溯

## Never Do

- ❌ AI 填写 Insight 节（人沉淀私人知识）
- ❌ 编造来源/依据
- ❌ 缺节不标注（应写"暂缺"）
- ❌ 使用 `---` 分割线（callout + 标题已足够分隔）

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/knowledge-card-writing-guide.md` | 7 节写作要点（每节写法+常见错误） |
| `references/batch-rewrite.md` | 批量重写已有卡片流程 |
| `references/edge-cases.md` | 边界条件（素材不足/模糊概念） |
| `references/design-decisions.md` | 格式设计决策记录 |

## 产出管线

```
信息输入 → clip Raw → 知识蒸馏(7节) → 人内化(Insight) → Evergreen → AI 检索
```
