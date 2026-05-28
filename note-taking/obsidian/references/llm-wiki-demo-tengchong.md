# llm-wiki 演示：腾冲 + 我的团长我的团

## 用户需求
用户想了解云南腾冲的历史，特别是与电视剧《我的团长我的团》的关联。

## 工作流执行记录

### Step 1: 存 raw sources

```bash
mkdir -p _wiki/raw/articles
# 腾冲 wiki
_wiki/raw/articles/tengchong-wikipedia-2026.md
# 团长 wiki
_wiki/raw/articles/my-colonel-my-brother-wikipedia.md
```

### Step 2: 写概念/实体页

```bash
mkdir -p _wiki/concepts _wiki/entities
# 概念页
_wiki/concepts/腾冲历史.md       # 更新：加入抗战和团长关联
_wiki/concepts/我的团长我的团.md # 新增
# 实体页
_wiki/entities/龙文章.md         # 新增
_wiki/entities/虞啸卿.md         # 新增
```

### Step 3: 更新 index + log

```bash
_wiki/index.md    # 添加新页面
_wiki/log.md      # 记录本次操作
```

### Step 4: 与已有笔记互链

已有笔记 `_wiki/概念页/腾冲.md` → 添加指向 `[[腾冲历史]]` 和 `[[我的团长我的团]]` 的 wikilink

## 关键技巧

### wiki 搜索技巧
```bash
# 通过维基百科 API 获取英文条目（绕过中文编码问题）
curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=Tengchong&prop=extracts&explaintext&format=json"

# 中文条目
curl -s "https://zh.wikipedia.org/w/api.php?action=query&titles=我的团长我的团&prop=extracts&explaintext&format=json"
```

### 跨 wiki 链接
已有 Obsidian 笔记（非 wiki 目录）也要和 wiki 页面互链：
```markdown
> 相关页面：[[腾冲历史]]（完整 wiki 概念页）
```

### frontmatter 必填字段
```yaml
---
title: 标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | entity | comparison
tags: [标签1, 标签2]
sources: [_wiki/raw/articles/源文件.md]
confidence: high | medium | low
---
```

### wikilink 最低要求
每个页面至少 2 个 `[[wikilinks]]` 指向其他 wiki 页面。孤立页面不会被链接网络发现。

## 实体 vs 概念区分
- **实体**：人物、地点、组织（龙文章、腾冲、虞啸卿）
- **概念**：主题、事件、理论（腾冲历史、我的团长我的团）
- **对比**：同一主题的 A/B 分析
