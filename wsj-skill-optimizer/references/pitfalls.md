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
