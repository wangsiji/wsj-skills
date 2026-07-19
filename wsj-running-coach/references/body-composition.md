---
name: body-composition
description: COROS 体重数据现状——非官方 API 无体重，但官方 MCP queryUserInfo 已接入自动拉取；体脂秤方案仍搁置
---

## COROS 体重数据说明（2026-07-19 更新）

**非官方 `coros-mcp`（cygnusb）无体重接口**（2026-06 全面探测结论，仍成立）：
- Web API（teamcnapi）：dashboard/analyse/dayDetail 共 50+ 字段，全运动指标，无体重
- Mobile API（apicn）：statistic 类型 1~100 全探测，body/weight 路径 16 个，全无数据
- `/user/getUserWeight` 返回 500

**但官方 MCP（`mcpcn.coros.com/mcp`）的 `queryUserInfo` tool 返回体重（kg）**——2026-07-19 已成功接入并接入 cron。
- 复用 `cmoron/coros-cli` 的 OAuth（Dynamic Client Registration + PKCE），用户浏览器点一次同意
- 封装：`coros-mcp/coros_weight.py`，token 存 `~/.hermes/coros_mcp_token.json`
- cron 每天 10:00 拉 `get_weight_kg()` 写 `体重数据.md`（同日去重）
- ⚠️ 无"每日称重历史序列"tool，返回 profile 最新值；cron 每日快照即可
- 完整流程/踩坑见 `references/coros-official-mcp-weight.md`

> **纠正旧结论**：此前 `body-composition.md` 写"COROS API 无体重字段，请勿重测"——该结论仅适用于**非官方 API**。官方 MCP 有体重，已可用，**不要再据旧结论拒绝接体重**。

## 身体成分数据（体脂秤，仍搁置）

⚠️ 体脂/身体成分自动化仍未解决（2026-06 探测后搁置）。体重本身已通过官方 MCP 解决，体脂仍需手动。

| 工具/方法 | 状态 | 原因 |
|-----------|------|------|
| SmartScaleConnect + 密码登录 | ❌ | Xiaomi API 返回 10025，需设备验证 |
| SmartScaleConnect + 扫码 | ❌ | 二维码指向国际版，中国区账号「地区不支持」 |
| micloud Python 库 | ❌ | 同样 70016 + 10025 |
| Playwright 自动化 SPA 登录 | ❌ | 新登录页仅显示国际社交登录，无短信入口 |
| 米家 App 内提取 Token | ❌ | iOS 无开发者模式 |
| **COROS 官方 MCP queryUserInfo（体重）** | ✅ **已接入** | OAuth DCR + PKCE，cron 自动 |
| Apple Health 导出（体脂） | ✅ 手动可行 | iPhone 健康 App → 导出 → 解析 XML |
| 用户口述/截图 | ✅ 随时可用 | 最简可靠 |

### 操作指引

当用户问"能不能获取体重数据"：
1. **体重**：直接用 `coros_weight.get_weight_kg()`（已自动化），或读 `体重数据.md`
2. **体脂/身体成分**：Apple Health 导出 或 用户口述；不要重复尝试已探明不可用的 Xiaomi 方案，除非环境变化
