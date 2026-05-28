# DBS 路由表 — 参考手册

本文档是 `dbs/SKILL.md` 中路由表的完整参考版本。

## 路由表总览

| 用户意图信号 | 路由到 | 一句话说明 |
|---|---|---|
| 想从多个视角讨论、说"帮我想想"、"听听不同观点"、"几个人讨论一下" | `/dbs-chatroom` | 定向聊天室，推荐或指定专家多角色讨论 |
| 带着具体商业问题、想看商业模式、说"我有个问题" | `/dbs-diagnosis` | 商业模式诊断，消解问题优先于回答问题 |
| 想找对标、想模仿谁、说"我该学谁" | `/dbs-benchmark` | 对标分析，五重过滤排除一切噪音 |
| 选题通过了想知道怎么做内容、说"这个内容怎么做" | `/dbs-content` | 内容创作诊断，五维检测 |
| 有短视频文案想优化开头、说"开头怎么写" | `/dbs-hook` | 短视频开头优化，诊断 + 生成方案 |
| 想起小红书标题、说"帮我起个标题"、要写标题 | `/dbs-xhs-title` | 小红书标题公式，75 个验证过的爆款公式匹配 |
| 发来文案问有没有 AI 味、说"检测一下" | `/dbs-ai-check` | AI 写作特征识别，只诊断不改 |
| 觉得自己在任何关键决策上走捷径、想找更深入的方法、说"有没有更慢的方法" | `/dbs-slowisfast` | 慢就是快，找到值得慢做的环节 |
| 知道该做什么但做不动、说"我总是拖延" | `/dbs-action` | 执行力诊断，阿德勒框架找到真正原因 |
| 某个概念搞不清楚、说"这个词什么意思" | `/dbs-deconstruct` | 概念拆解，维特根斯坦式审查 |
| 明确提到 Claude Code、Codex、AGENTS.md、CLAUDE.md、skill bridge、工作台迁移、双端统一，或说"我的 Agent 工作台很乱"、"帮我统一 Claude 和 Codex" | `/dbs-agent-migration` | Agent 工作台迁移，整理规则文件、真源、命名与 Claude / Codex 双端 bridge |

## 快速选择指南

当用户说...
- "帮我看看" → 问清楚哪个类型
- "我觉得我执行力有问题" → `/dbs-action`
- "我有个商业问题" → `/dbs-diagnosis`
- "我不知道该学谁" → `/dbs-benchmark`
- "帮我分析一下内容" → `/dbs-content`
- "开头怎么写" → `/dbs-hook`
- "起个小红书标题" → `/dbs-xhs-title`
- "有没有 AI 味" → `/dbs-ai-check`
- "有没有更慢的方法" → `/dbs-slowisfast`
- "拖延" → `/dbs-action`
- "这个词什么意思" → `/dbs-deconstruct`
- "迁移到 Codex/Claude" → `/dbs-agent-migration`

## 各 Skill 核心关键词

| Skill | 核心触发词 | 禁忌词 |
|---|---|---|
| dbs-action | 拖延、不做、知道但不做 | 加油、你很棒 |
| dbs-diagnosis | 商业模式、商业问题、赚钱 | 需要更多信息 |
| dbs-benchmark | 对标、学谁、模仿 | 我觉得 |
| dbs-content | 内容、选题怎么做 | 继续加油 |
| dbs-hook | 开头、视频文案 | - |
| dbs-xhs-title | 标题、小红书 | - |
| dbs-ai-check | AI味、检测 | 帮我改 |
| dbs-slowisfast | 慢、捷径、快方法 | 慢慢来 |
| dbs-deconstruct | 概念、词什么意思 | - |
| dbs-chatroom | 讨论、多视角 | - |
| dbs-agent-migration | 迁移、Claude Code、Codex | - |