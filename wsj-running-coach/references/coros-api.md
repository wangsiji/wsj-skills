---
name: coros-api
description: COROS Web/Mobile API参考：认证、活动/睡眠端点、已知陷阱与绕过方案
---

# COROS API 参考

## 认证

COROS 使用 Bearer Token + `accesstoken` header：
```
Authorization: Bearer {token}
accesstoken: {token}
```

**token 获取方式**：通过 Playwright 拦截 `teamcnapi.coros.com/activity/query` 请求，从请求头中读取。

**token 有效期**：约 30 分钟。登录后应立即捕获并使用。

---

## 活动数据

**端点**：`GET https://teamcnapi.coros.com/activity/query?size=20&pageNumber={n}&modeList=`

**认证**：需要 Bearer token + accesstoken

**响应字段**：`date`, `distance`(米), `adjustedPace`(秒/km), `avgHr`, `totalTime`(秒), `trainingLoad`, `name`, `sportType`

---

**睡眠数据 — 分两个 API，结论不同（2026-07-18 修正）：**

⚠️ **旧结论"睡眠 API 返回缓存值不可用"只对 Web API 成立，已过时。** 真实睡眠分期数据走独立的 **Mobile API**（`apicn.coros.com/coros/data/statistic/daily?type=4`），`cygnusb/coros-mcp` 的 `get_sleep_data()` 正是走这条通道，能拿到 deep/light/REM/awake 分期。

**Web API `dashboard/query` 的 sleep 字段确实存在缓存问题（仅此端点）：**
- 91 天历史数据所有 type 值**完全相同**（type13=3878, type14=11638, type16=21042）
- 说明该端点返回的是**缓存值/最后一次同步值**，非每日真实睡眠
- **type=16 不是"睡眠总时长"**，可能是核心睡眠（Deep Sleep）时长

**已验证 type 字段含义**（COROS PACE 3，2026年5月）：
- `type=13`: 3878秒 ≈ 1h04m → **浅睡（Light Sleep）**
- `type=14`: 11638秒 ≈ 3h14m → **深睡（Deep Sleep）**
- `type=16`: 21042秒 ≈ 5h50m → **核心睡眠（Core Sleep）** = 浅睡 + 深睡
- `type=101`: 88780秒 ≈ 24h39m → 全天时长
- `type=102`: 647秒 ≈ 10m47s → 清醒时间

**正确做法（2026-07-18 起）：** 日报睡眠不再靠用户口述兜底——优先用 `coros-mcp get_sleep_data(weeks=1)` 拿真实分期；若 mobile token 过期/未认证，再退回口述。Web API `dashboard/query` 的 sleep 字段**不要用于趋势**。

**推荐验证方案**：下次用户同步手环后，让用户截图COROS App睡眠详情页，从截图读取真实值，与 mobile API 字段对比确认对应关系。

---

## ⚠️ 已知陷阱

### 1. Login URL 含 dash-board
COROS 登录页 URL：
```
https://training.coros.com/login?lastUrl=%2Fadmin%2Fviews%2Fdash-board
```
`wait_for_url("**/dash-board**")` 会立即匹配，**错误通过登录等待**。

**修复**：用 Lambda 等待离开 login 页面：
```python
page.wait_for_url(lambda url: "login" not in url, timeout=60000)
```

### 2. 非运动日睡眠数据缺失
`sportType=200` 的骑行记录才有完整睡眠数据，普通跑步日可能无睡眠。

### 3. API 端点：trainingcn.coros.com 而非 teamcnapi.coros.com
睡眠数据接口 `trainingcn.coros.com` 可用，`teamcnapi.coros.com` 是活动数据接口。混用会导致 403。

### 4. COROS 登录页元素选择器
`input[type="email"]` 在部分版本找不到，需用备用选择器：
- `input[type="text"]`
- `input[placeholder*="邮箱"]`
- `input[placeholder*="email"]`

`button[type="submit"]` 可能需改为 `button:has-text("登录")` 或 `button:has-text("Sign in")`

### 5. Vision 工具不可靠
`vision_analyze` 有时不返回结果（同一张图片 MD5 相同但模型时而能读时而不能）。**COROS App 截图验证时，让用户直接口述/打字数值**，比依赖 vision 更可靠。

### 6. 前台超时限制
cron/shell 前台进程有 60 秒超时，COROS 登录约需 40–50 秒，偶尔更慢。

**解决**：多试一次即可成功。如果频繁超时，用后台进程：
```bash
nohup python3 /home/wangsiji/.hermes/skills/custom/running-coach/scripts/running_coach.py --days 7 > /tmp/sync.log 2>&1 &
```

### 7. 睡眠数据误区
见上方睡眠数据章节。**Web API `dashboard/query` sleep 字段不可用于趋势；Mobile API `type=4` 才是真实睡眠分期来源。**

---

## 体重数据不存在

**2026-06-01 全面探测结论：COROS API 不提供任何体重/体成分数据。**

### 探测范围

通过 coros-mcp（逆向 COROS 移动端 API）验证了以下路径：

**Web API**（`teamcnapi.coros.com`）：
- `/dashboard/query` — 23 个字段（HRV、RHR、训练负荷、VO2max…无体重）
- `/analyse/query` — 每日指标+VO2max，无体重
- `/analyse/dayDetail/query` — 34 个字段（配速、心率、负荷…无体重）
- `/user/getUserWeight` — 返回 500 Internal Server Error
- `/user/weight/query` — 返回 500 Internal Server Error

**Mobile API**（`apicn.coros.com`）：
- `/coros/data/statistic/daily?type=1~100` — 所有 type 值均无数据
- 16 个不同 body/weight 路径模式 → 全部 404
- 已知可用端点：`/coros/data/statistic/daily?type=4`（睡眠）

**结论：COROS 只在 App 端存储体重数据，不通过 API 暴露。** 当用户提出"从高驰获取体重"时：
1. 告知 COROS 无此接口
2. 推荐米家体脂秤（SmartScaleConnect）方案
3. 或用户通过手机截取 COROS App 体重记录页

---

## coros-mcp 工具参考

`~/projects/coros-mcp/` 是一个 MCP 服务器（`cygnusb/coros-mcp`），逆向了 COROS 移动端 API，用于程序化访问 COROS 数据。比 Playwright 脚本更稳定，但覆盖范围不同。

### 认证

虚拟机环境 `.venv/`，区域 cn。已通过调用 `login()` 完成双 token（web + mobile）存储。

### 架构

- `coros_api.py` — 所有 HTTP 逻辑，两套 API（Training Hub + 移动端）
- `auth/storage.py` — token 存储（keyring / 加密文件）
- `cache/` — SQLite 本地缓存层
- `models.py` — Pydantic 数据模型

### 可用数据

| 数据类型 | coros-mcp 工具 | 说明 |
|----------|---------------|------|
| 活动列表 | `list_activities` | 日期范围查询，含配速/心率/负荷 |
| 活动详情 | `get_activity_detail` | 单活动完整数据（含区间） |
| 每日指标 | `get_daily_metrics` | HRV、RHR、VO2max、训练负荷 |
| 睡眠 | `get_sleep_data` | **真实深浅睡分期（Mobile API type=4），可用** |
| 训练计划 | 读写全套 | 模板/排程/力量训练 |
| 体重 | ❌ 无 | 同上结论 |

### 手动请求端点

| 端点 | Token | 说明 |
|------|-------|------|
| `teamcnapi.coros.com/activity/query?size=20&pageNumber=` | web | 活动列表 |
| `teamcnapi.coros.com/analyse/dayDetail/query?startDay=&endDay=` | web | 每日指标（24周） |
| `teamcnapi.coros.com/analyse/query` | web | 综合指标+VO2max |
| `teamcnapi.coros.com/dashboard/query` | web | 面板汇总（sleep 字段为缓存值，勿用于趋势） |
| `apicn.coros.com/coros/data/statistic/daily?type=4&startDay=&endDay=` | mobile | **睡眠分期真实数据** |
| `apicn.coros.com/coros/data/statistic/daily?type=1~100` | mobile | 全部无效（无体重数据） |

### 注意事项

- mobile token 有效期 ~1 小时，可自动刷新（重放已存储加密登录 payload）
- web token 有效期 24 小时
- 中国区使用 `cn` 区域（→ `teamcnapi.coros.com` + `apicn.coros.com`）
- 登录 `login(skip_mobile=True)` 跳过移动端认证（不打断手机 App 登录状态）
