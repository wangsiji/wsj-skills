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

## 依赖与实现

- 复用 `cmoron/coros-cli`（GitHub）的 OAuth 实现：`oauth.py`(register_client/exchange_code/refresh_access_token) + `metadata.py`(MCP_ISSUERS: us/eu/cn) + `pkce.py` + `models.py`
- 安装到 coros-mcp 的 venv：`pip install -e .`（在克隆的 coros-cli 目录里）
- 封装模块：`coros-mcp/coros_weight.py`，token 持久化 `~/.hermes/coros_mcp_token.json`（含 `expires_at`）
- 调用：`asyncio.run(get_weight_kg())` → float kg（失败返回 None）；内部 `_ensure_token` 到期前自动 refresh

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
