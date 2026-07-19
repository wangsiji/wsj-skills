---
name: wsj-skill-optimizer
description: 优化 Hermes Agent 自建 skill 的结构与规范性。当用户要求"优化 skill""规范 skill""整理自建 skills"，或发现某 skill 行数膨胀(>600字)/frontmatter 缺字段/references 断链时使用。对齐 Anthropic 官方 Agent Skills 规范与 Hermes v2 范式（黄金条/优先级/Router/Never Do/检查表），覆盖前端元数据补齐、description 场景化、巨型 skill 下沉、v2 架构重构全流程。
version: 2.1.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skill, optimization, structure, hermes, maintenance]
    category: hermes
---

# Skill Optimizer（v2 路由版）

> 主文件只做路由。优化流程的 Step 1-7 详情、陷阱清单、研究日志下沉到 `references/`，按需读取。

## 黄金 5 条

1. 改前必备份 — `cp SKILL.md SKILL.md.bak.$(date +%Y%m%d)`
2. 磁盘真值 > 索引数字（`ls */d | wc -l` 而非旧统计）
3. description 是路由第一匹配依据——场景化长描述，非短句
4. 规则冲突时按 Rule Priority 裁决（P0 安全 > P4 格式偏好）
5. 只删冗余/重复/过时/断链内容，保留有效信息（经验资产不删）

## Rule Priority

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | 数据安全 | 改前备份；不改 vault 任务/日志；git 脏状态不 commit |
| **P1** | 路由准确性 | description 场景化 > triggers 精确词 > 默认不匹配 |
| **P2** | 结构清晰 | 主文件 ≤200 行（知识库→references），无重复定义 |
| **P3** | 引用完整 | references 指针 0 断链 |
| **P4** | 格式规范 | frontmatter 完整、验证清单交付前必过 |

## Task Router

```
用户说"优化 skill / 规范 skill / 整理 skills / 提交 skills 到远程 / 同步自建 skills 到 GitHub"
  ↓
A 新 skill 对齐官方范式
  → Step 3(description) + Step 4(When to Use/Prerequisites) + Step 2(frontmatter)
B 现有 skill frontmatter 缺字段
  → Step 2 补元数据（version/author/license/metadata）
C 巨型 skill (>600行)
  → Step 5 references 下沉 + Step 7 v2 架构重构
D 1000+ 行膨胀 skill（规则分散、重复定义）
  → Step 7 v2 架构重构（黄金条/Priority/Router/协议/Never Do/检查表）
E 引用校验
  → Step 6 断链检查
F 读官方范式
  → references/github-research.md + official/ 范例
G 推送/同步自建 skills 到远程仓库（含定时任务）
  → references/pitfalls.md 的"本地 nested vs 远程 flat 推送污染陷阱" + 镜像推送链路
```

## 输入输出协议

**输入**：skill 名称 + 问题描述（行数膨胀/缺字段/断链/规则分散）
**输出**：修改后的 SKILL.md + references/ 文件 + 备份留存

## Pre-flight Check

- [ ] 待优化 skill 路径确认（`~/.hermes/skills/custom/<name>/SKILL.md`）
- [ ] 当前备份已留存
- [ ] 用户权限边界明确（**新建须批准，修改已有不须**）
- [ ] **权限铁律复核**：除非用户本轮明确说"建/新建/批准新建 skill"，否则绝不新建——自改进机制自动沉淀的 skill 一律视为违规，用户确认后 `rm -rf`
- [ ] 核查 skill 是否存在时用**全盘 `find ~/.hermes/skills`**，不只 `custom/`（自动建的常在 `creative/` 等其它 category）

## Post Check

- [ ] frontmatter 有效 + description 场景化长描述
- [ ] When to Use + Prerequisites 存在
- [ ] 主文件 ≤200 行（巨型已下沉）
- [ ] references 指针 0 断链
- [ ] 备份可回滚

## Never Do

- ❌ 不改前备份就直接改
- ❌ 用 `read_file()` 读后写回 `.md`（行号污染 → 用 `open()`）
- ❌ description 压成短句（应场景化长描述）
- ❌ 凭证内联明文（用环境变量/keyring）
- ❌ 删有效经验资产只为了压行数
- ❌ 未经用户明确批准新建 skill（含自改进机制自动沉淀的）；误判"不存在"——核查 skill 须全盘 `find ~/.hermes/skills`，不只 `custom/`

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/optimization-flow.md` | Step 1-7 完整流程（备份→fm→desc→WtU→下沉→校验→v2） |
| `references/pitfalls.md` | 踩坑清单（read_file 污染/明文/误报断链/路径/索引/GitHub） |
| `references/github-research.md` | 无 Firecrawl 时用 GitHub API + raw 抓取开源范式 |

## 参考

- **官方范例**：`native-mcp` / `github-repo-type` / `humanizer`
- **已优化样本**：8 skill 总计 3,631 → 1,099 行（-70%），0 断链

| skill | 前 | 后 | 说明 |
|-------|----|----|------|
| wsj-qiuqiu-content | 1085 | 128 | v2 路由+RULE集 |
| wsj-calculator-mini | 580 | 104 | 三段下沉+计算引擎 |
| wsj-knowledge-card | 462 | 89 | 写作指南下沉 |
| wsj-running-coach | 433 | 85 | 日报模板下沉 |
| wsj-card-visual | 383 | 89 | 4风格→1 guide |
| wsj-server-infra | 357 | 408 | v2块+保留配置 |
| wsj-clip | 195 | 102 | 去重闸门+merge坑 |
| wsj-graphic-thinking | 136 | 94 | 精简路由 |
