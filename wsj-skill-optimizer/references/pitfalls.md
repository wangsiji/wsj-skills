---
name: skill-opt-pitfalls
description: 优化 Skill 的陷阱清单——read_file污染/明文凭证/误报断链/路径漂移/索引vs真相/GitHub研究。
---

# 陷阱清单

## read_file 行号污染（最常踩）
绝不用 `read_file()` 读后写回 `.md`——每行前 `N|` 前缀会破坏 YAML/markdown。用 `open()` 或 `terminal` 内 Python。

## 明文凭证
skill 内不得内联密码/API key。对 COROS 等需要认证的服务，用 `coros-mcp auth`（token 存 keyring）或环境变量，文档里只写"从环境变量读取"。

## 误报断链
grep 匹配到文档内的示例文字（如"详见 references/xxx.md"）会误判。需排除 `xxx.md` 占位后再校验。

## 路径漂移
- 脚本路径写 `custom/running-coach/` 而非 `productivity/`（旧路径已废弃）
- vault 引用用真实路径（`03-Resources/Notes/运动周追踪表.md` 而非 `Routine/`）
- 修改后 `grep` 自行确认

## 索引 vs 真相
批量改 vault 前重测真实状态（`ls Raw/ | wc -l`），不信过期 Active.md 统计或会话早期快照——磁盘是真值，索引是缓存。

## web_search / web_extract 不可用
本环境无 Firecrawl 额度。要"去 GitHub 学范式"时改用 GitHub API + raw 文件抓取：

```bash
# 搜仓库
curl -s "https://api.github.com/search/repositories?q=COROS+api&sort=stars"
# 读仓库文件
curl -s "https://raw.githubusercontent.com/anthropics/skills/main/spec/agent-skills-spec.md"
# 列目录
curl -s "https://api.github.com/repos/anthropics/skills/contents/skills"
```

勿在 web_search 上重试循环（每次 `401/403` 确认是额度问题）。

## 规则冲突未声明优先级
给 skill 加了多条规则但没有 Rule Priority → 模型在多规则冲突时随机取舍（qiuqiu-content 故障）。必须在主文件加 P0~P4 优先级表。

## description 误压缩成短句
官方范式要求场景化长描述（做什么 + 何时触发）。短 description 降低路由命中率，曾花一整天纠正 8 个 skill。

## 本地 nested 仓库 vs 远程 flat 仓库（推送污染陷阱）
**现象**：自建 skills 的远程 `wsj-skills` 是**平铺单库**（9 个 `wsj-*` 在仓库根 + README，远程独有 `.bak` 备份）；本地 `~/.hermes/skills` 是 **nested 全量仓库**（含 creative/productivity 等系统 skills + `custom/wsj-*`）。若从 `~/.hermes/skills` 直接 `git push origin master`，会把 787 项系统 skills 变更全推上去，覆盖/污染远程精心整理的平铺结构 → **严禁**。

**识别**（推送前必查）：
```bash
git ls-remote <remote>
git ls-tree --name-only origin/main          # 顶层是 wsj-* 还是 custom/
git log --oneline origin/main -3             # 远程是否有"结构对齐"提交
```

**标准解法（镜像推送链路）**：
1. `git clone <remote> ~/projects/wsj-skills`（平铺镜像仓，与远程结构一致）
2. 同步：对 `custom/` 每个 wsj-* 目录 `rm -rf` 后整体 `cp -a`，根目录 README/`.bak` 不受影响（保留远程独有文件）
3. 在镜像仓 `git add -A && commit && push origin main`

**DRYRUN 副作用**：同步动作（`rm -rf`+`cp -a`）会真实改写镜像仓，必须包在 `if [ "$DRYRUN" = "0" ]; then ... fi` 内，否则空跑也改状态。

## 自改进机制自动建 skill（HARD RULE 违规）
**现象**：对话中可能触发 Hermes 的 self-improvement / review 机制，自动从对话沉淀出 skill 并写入 `~/.hermes/skills/<category>/`（如 `creative/wsj-geo-map`），**未经用户批准**。这违反用户「未经明确批准不得新建任何 skill」的 HARD RULE。

**识别**（用户问"是不是又建了 skill"时，必须全盘查，不能只查 custom/）：
```bash
find ~/.hermes/skills -iname '*<关键词>*'          # 全盘搜，不只 custom/
ls -la ~/.hermes/skills/custom/                    # 看 9 个 wsj-* 是否异常增多
git -C ~/.hermes/skills/custom log --oneline | head   # 远程推送历史里有无新 skill
```
注意：自动建的 skill 可能在任意 category（creative/official/...），**不在 custom/**，只看 custom/ 会误判"不存在"。

**处理**：用户确认删除后直接 `rm -rf` 该目录；它在全量仓库下、未进 `custom/` 推送链，删了不影响远程 `wsj-skills`。删后全盘再 `find` 确认无残留、`custom/` 数量不变。

**根因提示**：self-improvement review 机制可能仍会自动建。若反复出现，应查触发源（某自改进 prompt / 配置）并加限制，而非每次手动删。

**真实案例（2026-07-19）**：旅居地图对话后，self-improvement review 自动建出 `creative/wsj-geo-map`（v1.1.0，内容覆盖"独立 HTML 地图 + Obsidian Map View 内联"两模式）。当时 agent 只 `ls custom/` 就否认"不存在"，用户质问后才全盘 `find` 发现。用户判定违规，`rm -rf creative/wsj-geo-map`。结论：自动沉淀的 skill 一律视为违规，无论内容多贴切。

## 检查 skill 是否存在：全盘搜，不只 custom/
**陷阱**：`~/.hermes/skills` 是全量 nested 仓库，分 `custom/`（自建9个wsj-*）、`creative/`、`productivity/`、`official/` 等。被问"X skill 在吗"时，若只 `ls custom/` 就下结论，会漏掉其他 category 下的同名/相关 skill，导致误报"不存在"。**规则**：凡核查 skill 存在性，必用 `find ~/.hermes/skills -iname '*<name>*'`（或至少搜含目标名的全树），再下结论。

## 中文名文件批量提交（pathspec 规避引号转义）
vault/笔记含中文路径，`git add '中文文件.md'` 在脚本里会被引号转义出错。改用**目录 pathspec** 按 vault 分区批量提交：
```bash
git add "03-Resources/Weread/" "00-LLM-WiKi/Raw/" "02-Areas/"
# 逐个分区 commit，无变更则跳过
```
变更按 `git status --porcelain -uall` 顶层目录归类，与分区一一对应提交。

## 每日定时提交脚本范式（cron 复用）
`~/.hermes/scripts/daily_vault_commit.sh` 可用作模板：
- 双仓库分别处理，各自「无变更 → 跳过」不产生空 commit
- 第二大脑：`git add -A → commit → push origin main`
- 自建 skills：走镜像推送链路（见上）
- 头部 `set +e` + `DRYRUN=${DRYRUN:-0}`，cron 调 `bash script.sh`，stdout 原样回执
- 提交信息带时间戳 `📅 每日自动提交 <ts>` 便于追溯
