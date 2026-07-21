# 批量重写已有卡片 · 会话记录

> 2026-07-09 会话：将 8 张学习/记忆类旧卡片重写为 7 节新格式。
>
> 旧卡片来自 `~/projects/wsj-second-brain/03-Resources/Evergreen/`

## 涉及的 8 张卡片

1. 必要难度理论
2. 艾宾浩斯遗忘曲线
3. 西蒙学习法
4. 库伯学习圈
5. 蔡格尼克记忆效应
6. DIKW
7. 学习力
8. 爬行脑更加喜欢视觉化的信息

## 重写流程

```
Step 1: search_files + read_file → 读取所有源卡片
Step 2: 逐张将旧内容映射到新格式 7 节
Step 3: 合并输出到同一文件（知识卡片-重写.md）
Step 4: 验证结构
  - grep -c "^### 卡片：" → 8
  - grep -c "^---$" → 16（8 对 frontmatter 分隔符，无多余 `---`）
  - grep -c "⚠️ 此部分由你填写" → 8
```

## 新格式模板

### Frontmatter（简化版）

```yaml
---
name: 核心词
description: 一句话结论（完整立场句）
category:
  - "[[常青卡片]]"
tags: [常青卡片]
source: []
status: learning
---
```

✅ 仅保留 6 字段。不保留 `source_type`/`confidence`/`created`/`modified`。

### 7 节结构

| 节 | 标题格式 | 必备内容 |
|----|---------|---------|
| Problem | `[!warning]` callout | 「你以为 vs 实际」表格（2 列 3 行） |
| Concept - 定义 | `### 📖 定义` | 一句话定义，核心加粗 |
| Concept - 本质 | `### 🔍 本质` | 底层机制分析 |
| Concept - 来源 | `### 🔬 来源与依据` | 提出者/理论 + 依据内容 表格 |
| Concept - 误解 | `### 🚫 常见误解` | ❌误解 vs ✅实际 表格 |
| Relation | 纯表格 | 类型/相关概念/关系说明 三列表（上位/相似/对立/应用） |
| Example | `[!example]` callout | 2-3 个案例，可内部嵌套 `[!tip]` |
| Action | `[!check]` callout | 步骤/动作/关键 三列步骤表 |
| Boundary | 纯表格 | ✅适用 vs ❌不适用 对比表 |
| Insight | `[!abstract]` callout | 三行模板表，留空 |

### Insight 留空模板

```markdown
> [!abstract] ⚠️ 此部分由你填写
> | 维度 | 你的回答 |
> |---|---|
> | 这句话刷新了我对…的认知 | |
> | 我打算在…场景用起来 | |
> | 一个更好的比喻来理解它 | |
```

### 节间规则

- ❌ **不用 `---` 分割线** — callout + 标题已足够分隔
- ❌ **卡片之间不用 `---` 分割线** — 靠 `### 卡片：` 标题自然分隔
- ❌ 不用居中标签

### 验证

```bash
# 卡片总数
grep -c "^### 卡片：" 输出文件

# frontmatter 分隔符（应为卡片数 × 2）
grep -c "^---$" 输出文件

# Insight 留空检查（应为卡片数）
grep -c "⚠️ 此部分由你填写" 输出文件

# 无多余字段检查
grep -cE "(source_type|confidence|created|modified)" 输出文件  # 应为 0
```
