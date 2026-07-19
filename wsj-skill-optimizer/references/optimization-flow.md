---
name: skill-opt-flow
description: 优化流程 Step 1-7 详情——官方范式、补元数据、description 场景化、When to Use、references 下沉、断链校验、v2 架构重构。
---

# 优化流程 Step 1-7（详情）

> 主文件只路由，详情在此。

## 官方范式（5 条）

1. **frontmatter 必填**：官方强制 `name` + `description`；`license` 是真实字段。Hermes 专属 `metadata.hermes.tags/category` 保留。
2. **description 场景化长描述（关键）**：路由第一匹配依据。应完整覆盖"做什么 + 何时触发"（见 Step 3 示例）。**不是短句**。
3. **When to Use**：自然语言触发场景（description 管路由、When to Use 管细节）。
4. **Prerequisites**：前置依赖/环境声明。
5. **结构分层**：决策逻辑在 SKILL.md，细节在 `references/`。官方用根目录大写在 `REFERENCE.md`；Hermes 用 `references/` 子目录，等价。

## Step 1 — 备份

```bash
cp -r ~/.hermes/skills/custom/<name> ~/.hermes/skills/custom/<name>.bak.$(date +%Y%m%d)
```

## Step 2 — frontmatter 补元数据

对缺 `version/author/license/platforms/metadata` 的 skill，在 `---\n...\n---` 内追加：

```yaml
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [<相关标签>]
    category: <health|knowledge|content|infra|dev|creative|productivity>
```

> 用 Python 解析 frontmatter（非正则硬切），保留已有字段不覆盖。

## Step 3 — description 场景化长描述

**不要压成短句。** 官方 pdf skill 示例：

```
Use this skill whenever the user wants to do anything with PDF files. This includes reading or
extracting text/tables from PDFs, merging/splitting/rotating pages, adding watermarks, filling
forms, OCR on scanned PDFs. If the user mentions a .pdf file or asks to produce one, use this skill.
```

> triggers 列表与 description 互补：description 管语义路由、triggers 管精确词命中。

## Step 4 — 加 When to Use + Prerequisites

在 `# 标题` 行后插入。

## Step 5 — 巨型 skill references 下沉

当 SKILL.md > 600 行，按 `## ` 段切分：
- 认知框架/理论底座 → `references/<topic>-mindset.md`
- 服务详细配置/工具细节/数据表 → `references/<topic>.md`
- 主文件原位替换为 1-2 行指针：`> 详见 references/<x>.md`
- 切分用 Python 精确切片，禁 read_file 行号污染
- 同类内容合并为更少文件（如 4 个风格文件→1 个 style-guide.md）

## Step 6 — 断链校验

```bash
cd ~/.hermes/skills/custom/<name>
for ref in $(grep -ohE "references/[a-zA-Z0-9_-]+\.md" SKILL.md | grep -vE "xxx\.md" | sort -u); do
  [ -f "$ref" ] && echo "OK $ref" || echo "❌ 缺失 $ref"
done
```

> 排除文档示例占位（`references/xxx.md` 说明文字），只校验真实引用。

## Step 7 — v2 架构重构

当 skill 规则分散多处、模型"读懂但执行变慢"时执行。核心目标：主文件从"知识库"→"路由 + 决策引擎"（≤200 行），细节下沉 references。

**v2 范式块**（加在 When to Use 之后）：
1. 黄金 N 条 — 每次默念（≤10 条）
2. Rule Priority — P0~P4 分层裁决
3. Task Router — 先分类（A~G）再执行
4. 输入输出协议 — task/topic/audience/goal/tone
5. Pre-flight Check — 生成前检查
6. Post Check — 生成后检查（小 skill 可省）
7. Never Do — 禁止行为集中

**附加值操作**：
- 踩坑记录从故事 → RULE 可执行条目（qiuqiu RULE-01~20）
- 分散的禁止/不要/❌ → Never Do + RULE 集
- 编辑历史 → `references/editorial-history.md`
