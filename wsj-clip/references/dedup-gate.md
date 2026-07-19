---
name: clip-dedup-gate
description: 剪藏前 vault 状态校验与去重闸门。批量写前先重测真实状态，不盲改。
---

# 去重闸门（批量写前必做）

剪藏/整理涉及对 vault 的批量写时，先重测真实状态，不盲改：

```bash
VAULT="/home/wangsiji/projects/wsj-second-brain"
find "$VAULT" -name "*.md" -not -path '*/.git/*' -not -path '*/.obsidian/*' | wc -l
git -C "$VAULT" status --short | sed -E 's/^([A-Z ]).*/\1/' | sort | uniq -c
```

- **`Active.md` 的"统计"段会失真**：用户主动清理信源目录后，索引仍写旧数字（如"57 篇"），磁盘真实篇数已变。信 `ls Raw/ | wc -l` 真值，不信索引。
- 会话早期盘点数字 ≠ 当前真值，每次批量写前重测。
- `git status` 大量 ` D`（两空格 D = deleted，磁盘没了 git 还记着）通常是用户**主动清理**的已知结果，不是损坏——但脏状态下**不要 `git commit`**，除非用户明确许可。

## 提交 URL 前先查重

用户曾要求剪藏 `lijigang/ljg-skills`，而 `Raw/李继刚/ljg-skills/` 已在库内（44 文件）。避免同一会话重复灌入已知信源。

```bash
# GitHub 仓库：规范化 owner/repo 后在 Raw/ 下检索
repo=$(echo "<url>" | sed -E 's#.*github.com/([^/]+)/([^/?#]+).*#\1/\2#')
ls 00-LLM-WiKi/Raw/ | grep -iE "GitHub_.*${repo##*/}" && echo "已存在"
# 通用：用标题关键词在 Raw/ 下检索（search_files 工具）
search_files(pattern="<关键词>", path="00-LLM-WiKi/Raw")
```

命中即三选一：
- **① 跳过**（最常用，符合"建得起清得掉"纪律）
- **② 更新**（仅确认远程有新增时，diff 增量，不整篇重抓）
- **③ 转消化**（把已存在的源当作主题合成的素材，比再剪新仓库值钱）

这步呼应知识系统理念：采集速度常快于消化，重复剪藏是"采集态待太久"的信号。
