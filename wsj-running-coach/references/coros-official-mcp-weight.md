---
name: coros-official-mcp-weight
description: 如何拿到 COROS 体重——官方 MCP (queryUserInfo) 的 OAuth 流程、cmoron 依赖、token 持久化与 cron 接入。非官方 API 无体重，官方 MCP 才有。
---

# COROS 体重 = 官方 MCP `queryUserInfo`

> 非官方 `coros-mcp`（cygnusb）的所有 endpoint（web `/analyse/dayDetail`、`/analyse/query`、`/dashboard/query` + mobile `/coros/data/statistic/daily` 各种 type）**均不含体重字段**（已枚举确认）。
> 体重只在 **COROS 官方 MCP server** 的 `queryUserInfo` tool 里返回（单位 kg）。

## 关键事实

- 官方 MCP issuer（中国区）：`https://mcpcn.coros.com`，MCP endpoint = `{issuer}/mcp`
- OAuth 方式：**Dynamic Client Registration (RFC 7591) + PKCE (S256)**——无需预注册 app，现场向 `/connect/register` 注册 public client
- `queryUserInfo` 返回：`Height / Weight(kg) / Birthday / Gender / Nickname`
- ⚠️ **没有"每日称重历史序列"tool**：体重是 profile 字段，返回的是你 App 里设的**最新值**。cron 每天拉一次 = 每日快照，正好够用
- `queryDailyHealthData` 有步数/卡路里/睡眠/压力，**但不含体重**（已验证）
- `queryHealthCheckTimeSeries` 是"健康打卡"序列，你不打卡就无数据

## 官方 MCP 能力边界（关键，避免重复踩坑）

> 不要试图把跑步/俯卧撑/训练计划也迁到官方 MCP —— **动态注册的 public client 被官方网关限流，运动记录类 tool 调不通**。

- ⚠️ `querySportRecords`（跑步/俯卧撑活动）、`queryTrainingSchedule`（训练计划）等**大数据量 tool 被官方 MCP 网关拒绝**，返回：
  `"Tool call anomalies detected... request exceeds the LLM capability boundary..."`
  原因：Dynamic Client Registration 的 public client 权限受限，官方只放开了 profile/轻量查询。
- ✅ 实测**只有 `queryUserInfo`（体重）能稳定返回**；`queryDailyHealthData` 等轻量 tool 可用但**不含体重**。
- 运动记录/计划仍走**非官方 coros-mcp**（`fetch_activities` / `fetch_schedule`，中国区网络偶发超时需重试）。
- 若将来要解锁官方 MCP 全部 22 个 tool → 需要 **COROS 官方审核发放的 OAuth app（client_id/secret）**，不是现场动态注册能拿到的。
- ⚠️ 当前 token 是 public client 动态注册所得，COROS **随时可能 revoke** 此 client；若某天 `coros_weight.get_weight_kg()` 失败，大概率是 client 被 ban，回退手动记或重新走一次 OAuth 流程。

## 依赖与实现（2026-07-20 重写为自包含）

> ⚠️ **历史版本依赖 `cmoron/coros-cli`**（pip install -e 装进 coros-mcp venv）。**当前版本已重写为自包含**，不再 import cmoron —— 直接 HTTP 调官方 MCP endpoint，自己实现 Dynamic Client Registration + PKCE。原因：提上游 PR 时不能引第三方包；自包含版 `coros_weight.py` 仅依赖 `httpx`（coros-mcp 已有）。

- 封装模块：`coros-mcp/coros_weight.py`（自包含），token 持久化 `~/.hermes/coros_mcp_token.json`（含 `expires_at`）
- 对外函数：
  - `asyncio.run(get_weight_kg())` → float kg（失败返回 None）；内部 `_ensure_token` 到期前自动 refresh
  - `asyncio.run(prepare_auth())` → dict(url, state, verifier, client_id, client_secret)，打印授权 URL 给用户
  - `asyncio.run(complete_auth(code, meta))` → 用回调 code 换 token 并持久化
- 调用：`asyncio.run(get_weight_kg())` 即可；未授权时返回 None 并打印提示。

## OAuth 流程（一次性，需用户交互）

1. `register_client(http, meta)` → 拿到 `client_id`
2. `build_authorization_url(meta, client, state, code_challenge)` → 生成授权 URL
3. **用户浏览器打开 URL，登录 COROS 点同意** → 跳转 `http://localhost:8765/callback`（会连不上，正常）
4. 用户把地址栏完整 URL（含 `?code=...&state=...`）发回
5. `extract_authorization_code(pasted, state)` + `exchange_code(...)` → `access_token`(~30天) + `refresh_token`
6. 持久化 token（含 client_id/secret/verifier/state/各 endpoint）

## 踩坑

- **refresh_token 偶发 500**（COROS 服务端不稳）：`refresh_access_token` 要包 **3 次重试**，单次失败不算死
- 授权码 `code` 有效期极短（几分钟），拿到 URL 尽快操作；过期重跑阶段1生成新 URL
- `access_token` 约 30 天有效，cron 里每日先试 refresh，refresh 失败告警让用户重新授权一次（不要静默失败）
- web_search 在本环境**未配置**（无 Firecrawl key），搜 API 改用 `gh` CLI + `git clone` + `grep`（cmoron 就是这么找到的）

## 接入 cron

`_cron_sync_coros.py`（每天 10:00）在拉完跑步/俯卧撑后，用子进程调 `coros_weight.get_weight_kg()`，
把 `kg×2` 写进 `体重数据.md`（同日去重：已有该日期行则覆盖）。体重失败不影响跑步/俯卧撑写入（try/except 隔离）。

## 上游 PR 流程（贡献回 coros-mcp，可复用）

`coros_weight.py` 最初在本地 `~/projects/coros-mcp`（cygnusb 上游 clone）加的，本地 commit 后 `git push origin main` **被拒（403，无上游写权限）**。正确贡献流程（2026-07-20 实测）：

1. `gh repo fork cygnusb/coros-mcp --clone=false` → 在你的名下建 `wangsiji/coros-mcp`（若已存在则跳过）
2. `git remote add wangsiji https://github.com/wangsiji/coros-mcp.git`
3. 从本地 main 切**新分支**：`git checkout -b feat/weight-official-mcp`（不要直接推 main，远端 main 有上游新提交会 rejected non-fast-forward）
4. `git push wangsiji feat/weight-official-mcp`
5. `gh pr create --repo cygnusb/coros-mcp --head wangsiji:feat/weight-official-mcp --base main --title "..." --body "..."`
   - PR body 必须写清：**动机**（非官方API无体重字段）、**改动**（自包含实现/不引依赖/封装queryUserInfo）、**已知限制**（public client 限流、仅覆盖体重、与项目"无 key 非官方"定位的潜在冲突）
   - 本次 PR：`https://github.com/cygnusb/coros-mcp/pull/46`

> 提 PR 前确认改动**自包含、不引外部私有依赖**——上游不会接受 import 你本机 venv 里的第三方包。本地能用 ≠ PR 能合并。
