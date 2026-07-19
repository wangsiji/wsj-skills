# 知识卡设计演进 · 架构决策记录

> 本文档记录 knowledge-card skill 从 v1（模板）到 v4（个人知识引擎）的关键设计决策和背后原因。

---

## 版本演进

| 版本 | 核心变化 | 触发 |
|------|---------|------|
| v1 | 初始版 — 7 节模板 | 用户定义格式 |
| v2 | Darwin 优化 — 触发词、7 节写作指南、边界条件 | Darwin skill 评估 |
| v3 | **Insight 分离** + Concept 升级 + source/confidence | 用户架构评审 |
| v3.5 | **Frontmatter 精简** + 无标题行 + 无 `---` 分割线 + Callout 标准化 | 用户视觉优化反馈 |

---

## 关键架构决策

### 决策 1：Insight 不由 AI 生成

**问题：** AI 会假装理解用户。例如 AI 写「我以前以为学习只是输入，后来发现输出才是真正学习」——这不是用户的洞察，是 AI 根据训练数据生成的。

**决策：** AI 只生成 6 节（Problem/Concept/Relation/Example/Action/Boundary），Insight 输出留空模板，标注 `⚠️ 用户填写`。

**哲学：** "AI 负责整理知识，人负责产生认知。" 真正区分用户的，是哪些知识被用户的经历、判断和行动重新加工过。

### 决策 2：Boundary 放在 Insight 之前

**原因：** Boundary 属于公共知识，Insight 属于私人知识。顺序形成「世界知识 → 我的认知」的收束。

### 决策 3：Concept 层拆为四部分

- 定义（Definition）
- 本质（Essence）
- 来源与依据（Source & Evidence）
- 常见误解（Misconception）

**原因：** 知识库长期存在后，需要知道「这个知识凭什么可信」。若缺乏研究依据，标注「暂无明确研究依据，属于经验模型」。

### 决策 4：Frontmatter 精简（v3.5）

**问题：** `source_type` `confidence` `created` `modified` 四个字段每次改卡片都要更新，且大部分卡片不需要。

**决策：** 简化版 frontmatter 仅保留 `name/description/category/tags/source/status`。`source_type` `confidence` 作为可选扩展字段。

### 决策 5：无标题行（v3.5）

**决策：** 卡片以 frontmatter 后直接 `## 1. 问题` 开始，没有 `# 核心词` H1 标题。文件名已包含名称。

### 决策 6：无 `---` 分割线（v3.5）

**决策：** 全篇不用任何 `---` 分割线。callout 区块和 `## 节标题` 已足够视觉分隔。

### 决策 7：Callout 标准化（v3.5）

每节使用固定 callout 类型：Problem=`[!warning]`, Concept=纯标题, Relation=纯表格, Example=`[!example]`(+ `[!tip]`), Action=`[!check]`, Boundary=纯表格, Insight=`[!abstract]`。

### 决策 8：Pipeline 显式化

```
clip → knowledge-card → Human(Insight) → Evergreen → AI Retrieval
```

### 决策 9：案例优先级（禁止虚构用户经历）

**优先级：** 用户提供 > vault 记录 > 公开真实案例 > 类比
**红线：** 禁止写「你之前在跑步时发现…」等虚构用户经历。

### 决策 10：Relation 必须用 `[[wikilinks]]`

每个相关概念是 Obsidian 双链格式，不只是纯文本列表。

---

## 设计哲学

> **把互联网知识，通过 AI 蒸馏成结构化知识，再通过人的实践和反思，转化成个人资产。**
>
> **AI 提炼公共知识，人沉淀私人知识。**

---

## 与其他 skill 的关系

| 阶段 | Skill | 产物 |
|------|------|------|
| 📥 输入 | `clip` | Raw 剪藏素材 |
| 🧠 蒸馏 | `knowledge-card` | Evergreen 卡片 |
| 🎨 可视化 | `knowledge-card-visual` | 图形输出 |
