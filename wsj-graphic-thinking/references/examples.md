# 使用示例

## 示例 1：单图·树状图

**用户输入**：大理旅居的收入来源有哪些？

**过程**：
- problem_type: classification
- abstraction_level: low
- 匹配：② 树状图
- 输出：`2026-07-15-dali-income-tree.excalidraw.md`

## 示例 2：单图·深挖图

**用户输入**：为什么我的跑步成绩提升不了？

**过程**：
- problem_type: causal_analysis
- abstraction_level: low → middle
- 匹配：③ 深挖图
- 输出：`2026-07-15-running-fatigue-root-cause.excalidraw.md`

## 示例 3：单图·比较图

**用户输入**：对比 Obsidian 和 Notion 做第二大脑的优劣

**过程**：
- problem_type: comparison
- abstraction_level: middle
- 匹配：④ 比较图
- 输出：`2026-07-15-cross-platform-comparison.excalidraw.md`

## 示例 4：多图·复杂决策

**用户输入**：我在考虑把 Hermes 从 deepseek 换成 CloudBase 的 deepseek-v4-pro

**过程**：
- problem_type: value_exchange + process_mapping
- abstraction_level: middle
- 匹配：① 交换图（诊断当前→目标得失）+ ⑤ 流程图（迁移步骤）
- 策略：递进图（先诊断再方案）
- 输出：
  - `2026-07-15-provider-exchange.excalidraw.md`
  - `2026-07-15-migration-flow.excalidraw.md`

## 示例 5：系统图

**用户输入**：把我的第二大脑画成系统图

**过程**：
- problem_type: system_mapping
- abstraction_level: high
- 匹配：⑧ 系统图
- 输出：`2026-07-15-second-brain-system.excalidraw.md`

## 示例 6：知识卡片模式

**触发**：把这篇笔记画出来 / 生成知识图解

**过程**：
1. 读取卡片名称
2. 提取 7 节内容
3. 按映射规则匹配图形
4. 调用 main workflow 生成
5. 输出文件回链源卡片
