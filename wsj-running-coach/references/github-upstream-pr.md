---
name: github-upstream-pr
description: 把本地改动贡献回上游开源仓库的可复用流程（fork→分支→push→gh pr create），含自包含改动要求与 PR body 写法。
---

# 贡献改动回上游仓库（GitHub）

场景：你在本地 clone 了别人的开源仓库（如 `cygnusb/coros-mcp`），改了点东西想提 PR。直接 `git push origin main` 会被拒（403 无写权限）。

## 流程（实测）

1. **fork 到名下**（若还没 fork）：
   `gh repo fork <upstream> --clone=false` → 生成 `github.com/<你>/<repo>`
2. **加远端**：
   `git remote add <你> https://github.com/<你>/<repo>.git`
3. **切新分支**（不要推 main，远端 main 有上游新提交会 non-fast-forward rejected）：
   `git checkout -b feat/<topic>`
4. **推到你的 fork 分支**：
   `git push <你> feat/<topic>`
5. **开 PR**：
   `gh pr create --repo <upstream> --head <你>:feat/<topic> --base main \
     --title "feat: ..." --body "..."`

## PR body 必须写清（用户要求：改动要透明）

- **动机**：为什么需要这个改动
- **改动**：具体改了什么、怎么实现
- **已知限制**：边界、依赖、与上游定位的潜在冲突

示例（coros_weight.py 体重 PR #46）：
> 动机：非官方 API 所有 endpoint 均不含体重字段，体重仅在官方 MCP 的 queryUserInfo。
> 改动：新增 coros_weight.py，自包含（不引第三方 OAuth 包），封装 queryUserInfo。
> 限制：public client 被限流，仅覆盖体重；与项目"无 key 非官方"定位可能冲突。

## 关键坑

- **PR 改动必须自包含、不引外部私有依赖**：上游不会接受 import 你本机 venv 里的第三方包（如 `cmoron/coros-cli`）。提 PR 前把依赖内联/重写掉。本地能跑 ≠ PR 能合并。
- `gh` CLI 需先 `gh auth login`（本机已登录 wangsiji，token 在 `~/.config/gh/hosts.yml`）。
- 若 `gh repo fork` 静默无输出，用 `gh repo view <你>/<repo>` 确认 fork 是否真的建了。
- 分支名用 `feat/`、`fix/` 前缀，便于上游 review。
- ⚠️ **`gh pr edit --title/--body` 可能静默失败**：当仓库开启 Projects (classic) 时，`gh pr edit` 会报 `Could not resolve to a node id ... Projects (classic).write` 警告，且 **title/body 不被应用但命令仍 exit 0**（看起来成功实则没改）。本会话 PR #46 改英文标题/正文就踩了这个——`gh pr view` 仍显示旧中文标题。解决：用 `gh api` 直接 PATCH：`gh api -X PATCH /repos/<upstream>/pulls/<N> -f "title=..."`（body 同理 `-f "body=..."`）。纯改标题也可 `gh api -X PATCH .../pulls/N -f "title=feat: ..."`。
- 🌐 **非英文仓库提 PR：用户要求 PR 内容全英文**（title/body/commit message/代码注释）。改完先核：`grep -nP '[\x{4e00}-\x{9fff}]' <file>` 确认无中文残留再 push；amend 已提交的 commit 后需 `git push <你> feat/<topic> --force-with-lease`（个人 fork 分支允许 force）。
