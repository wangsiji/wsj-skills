---
name: wsj-graphic-thinking
description: 将案例/笔记/问题转换为结构化图解：当用户要求"画出来""可视化""图解"，或需分析系统结构、找原因复盘、比较方案、规划路径时，自动匹配树状图/流程图/深挖图/系统图，生成 Obsidian Excalidraw 图形（.excalidraw.md 格式）。
version: 2.2.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [diagram, excalidraw, thinking, visualization]
    category: creative
---

# Graphic Thinking Agent（路由版 v2）

> 主文件只做路由 + 最高优先级规则。细节在 `references/`，按需读取。

## 黄金 5 条

1. 先思考蒸馏（结构化 JSON）再画图，不直出图形
2. 图形类型由 P1~P5 优先级系统决定，冲突时展示方案确认
3. 每框 ≤10 字，无孤立节点，3 秒能理解
4. 输出 `.excalidraw.md`（## Drawing + ```json + %% 结尾），不压缩不编码
5. 洞察标注（Step 2.5）必加，图不是装饰是思考载体

## Rule Priority（图形冲突时）

| 优先级 | 规则 |
|--------|------|
| **P1** | 用户明确指定图形 → 直接用 |
| **P2** | 关键词匹配 problem_type 映射 |
| **P3** | 关系类型匹配（因果/对比/交换） |
| **P4** | 实体数量 → 5+ 推系统图/树状图 |
| **P5** | 兜底树状图 |

多图冲突 → 展示方案给用户确认，否则走递进图策略。

## Task Router

```
用户输入（案例/问题/卡片文件名）
  ↓
Step 0 意图判断（触发词匹配）
Step 1 接收输入（卡片模式→references/knowledge-card.md）
Step 1.5 思考蒸馏 → 结构化 JSON（problem_type/entities/relations/abstraction_level）
Step 2 图形决策（P1~P5 → references/graph-selection.md）
Step 2.5 洞察提取（本质/隐藏关系/矛盾/行动）
Step 3 生成 Excalidraw（格式→references/excalidraw.md，模板→references/templates.md）
Step 3.5 多图形协作（主图+副图/递进图）
Step 3.8 质量审查
Step 4 输出 .excalidraw.md → 00-Attachments/Excalidraw/
```

## 输入输出协议

**输入**：案例/笔记/问题文本，或知识卡片文件名
**输出**：`.excalidraw.md` 文件 + Markdown 图解说明

## Pre-flight Check

- [ ] 已思考蒸馏（非直出）
- [ ] problem_type 已确定
- [ ] abstraction_level 已定（low/middle/high）

## Post Check（质量审查）

- [ ] 核心问题回答用户原问？
- [ ] 每框 ≤10 字？无孤立节点？
- [ ] 节点数在图形类型默认范围？
- [ ] 3 秒理解？洞察标注已加？
- [ ] 全部 containerId 绑定？

## Never Do

- ❌ 跳过思考蒸馏直接画图
- ❌ 每框塞长句（信息堆积）
- ❌ 输出非 `.excalidraw.md` 格式（压缩/编码 JSON）
- ❌ 无洞察标注的纯装饰图

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/graph-selection.md` | P1~P5 图形决策 + 节点数限制 |
| `references/excalidraw.md` | Excalidraw 格式/字体/容器 |
| `references/templates.md` | 图形模板参数 |
| `references/knowledge-card.md` | 知识卡片集成模式 |
| `references/examples.md` | 使用示例 |

## 产出管线

```
输入 → 思考蒸馏 → 图形决策 → 洞察提取 → Excalidraw → Obsidian 知识资产
```
