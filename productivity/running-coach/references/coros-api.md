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

**睡眠数据 ⚠️ 严重警告：API 无法获取每日真实睡眠**

`dashboard/queryCycleRecord` 的 sleep 字段存在根本性问题：
- 91 天历史数据所有 type 值**完全相同**（type13=3878, type14=11638, type16=21042）
- 说明 API 返回的是**缓存值/最后一次同步值**，而非每日真实睡眠数据
- COROS App 显示 5h39m，但任何单一 type 字段都无法匹配
- **type=16 不是"睡眠总时长"**，可能是核心睡眠（Deep Sleep）时长

**已验证 type 字段含义**（COROS PACE 3，2026年5月）：
- `type=13`: 3878秒 ≈ 1h04m → **浅睡（Light Sleep）**
- `type=14`: 11638秒 ≈ 3h14m → **深睡（Deep Sleep）**
- `type=16`: 21042秒 ≈ 5h50m → **核心睡眠（Core Sleep）** = 浅睡 + 深睡
- `type=101`: 88780秒 ≈ 24h39m → 全天时长
- `type=102`: 647秒 ≈ 10m47s → 清醒时间

**严重问题**：91天历史数据所有type值完全相同，与COROS App显示的实际睡眠不符：
- App 5月3日显示：6h13m
- App 5月4日显示：5h39m
- API type16：均为 5h50m

API返回的是缓存值/最后一次同步值，**不能反映每日真实睡眠**，不能用于趋势追踪。COROS App截图对比是唯一验证途径。

**推荐验证方案**：下次用户同步手环后，让用户截图COROS App睡眠详情页，从截图读取真实值，与API字段对比确认对应关系。

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

### 4. Vision 工具不可靠
`vision_analyze` 有时不返回结果（同一张图片 MD5 相同但模型时而能读时而不能）。**COROS App 截图验证时，让用户直接口述/打字数值**，比依赖 vision 更可靠。

### 5. 前台超时限制
cron/shell 前台进程有 60 秒超时，COROS 登录约需 40–50 秒，偶尔更慢。

**症状**：超时退出，activities.json 数据停留在上一次成功抓取的时间点（本次 session：数据卡在 5月4日，实际 5月6日已有新活动）

**解决**：多试一次即可成功。如果频繁超时，用后台进程：
```bash
nohup python3 /home/wangsiji/.hermes/skills/productivity/running-coach/scripts/running_coach.py --days 7 > /tmp/sync.log 2>&1 &
```

### 6. 睡眠数据不可用
见上方睡眠数据章节。**日报中的睡眠部分：直接问用户昨晚睡了多久**，不要从 sleep.json 读取。
