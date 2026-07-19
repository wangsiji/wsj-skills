# 知识卡片集成

## 模式：知识卡片 → Excalidraw

automated when triggered by: 生成知识图解、知识卡片可视化、把这篇笔记画出来

### 映射规则

| 卡片字段 | → 图形类型 | 用途 |
|----------|:----------:|------|
| relation | 系统图/交换图 | 关系可视化 |
| case | 流程图/时间线图 | 案例复盘 |
| action | 流程图/金字塔图 | 行动规划 |
| problem | 深挖图 | 根因分析 |
| concept | 重叠图/树状图 | 概念对比 |
| boundary | 比较图 | 边界比较 |
| insight | 所有图形 | 核心标注 |

### 生成流程

1. 读取卡片 frontmatter（name/description/category/tags/source）
2. 读取卡片 7 节内容（problem/concept/relation/case/action/boundary/insight）
3. 按映射规则匹配图形
4. 输出 `.excalidraw.md`
5. 在输出文件 frontmatter 或注释中回链源卡片：`source: [[卡片名称]]`

### 输出路径

```
00-Attachments/Excalidraw/{卡片日期}-{卡片名称缩写}-{图形类型}.excalidraw.md
```

## 模式：Excalidraw → 知识卡片（反向链接）

在生成的 .excalidraw.md 文件的 frontmatter 中增加：

```markdown
---
excalidraw-plugin: parsed
source:
  - [[源卡片名称]]
graph_type: 深挖图
created_by: graphic-thinking
---
```
