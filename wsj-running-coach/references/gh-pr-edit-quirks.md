# gh pr edit 静默吞改的坑（Projects classic 弃用警告）

## 现象

给上游仓库提 PR 后想改标题/正文：

```
gh pr edit 46 --repo cygnusb/coros-mcp \
  --title "feat: fetch body weight via official COROS MCP (coros_weight.py)" \
  --body "..."
```

命令返回 exit 0，但只打印一行 GraphQL 警告：
> "GitHub Projects (classic) is deprecated and will be removed..."

再看 `gh pr view 46 --json title` —— **标题还是旧的（中文），body 也没变**。`--body` 同样被吞。

## 根因

`gh pr edit`（title/body 路径）内部走一个会触碰 Projects (classic) 字段的 mutation。当该 mutation 因 classic 弃用而警告/跳过时，title/body 的更新被一并跳过，且 `gh` **不硬失败**（exit 0），所以看起来"成功了"实则没生效。

## 修复（可靠路径）

绕过 Projects mutation，直接 PATCH：

```bash
# 改标题
gh api -X PATCH /repos/cygnusb/coros-mcp/pulls/46 \
  -f "title=feat: fetch body weight via official COROS MCP (coros_weight.py)"

# 改正文（可同一条，也可分开；body 用 heredoc/多行时引号转义要小心）
gh api -X PATCH /repos/cygnusb/coros-mcp/pulls/46 \
  -f "body=## Motivation
The unofficial API (web/mobile) exposes no weight field...
## Changes
- ...
## Known limitations
- ..."
```

`gh api` 直连 REST，不经过 Projects mutation，标题/正文必然落库。

## 关联

- 上游仓库若要求 PR 自包含（self-contained），body 写 Motivation / Changes / Known limitations 三段即可（英文仓库全英文）。
- PR 创建仍用 `gh pr create`（不受此坑影响）；只**编辑**走 `gh api PATCH`。
- 验证是否真生效：`gh pr view <N> --json title,body` 看实际值，别信 exit code。
