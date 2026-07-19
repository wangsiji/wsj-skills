---
name: coros-mcp
description: coros-mcp备用数据获取：安装、API端点、cron交互限制与Python程序化调用
---

> ✅ **2026-07-18 实测状态**：`coros-mcp auth`（region=asia）已认证，Web+Mobile 双 token 有效。
> - `get_sleep_data` → 真实睡眠分期（deep/light/REM/awake + 心率）
> - `get_daily_metrics` → HRV、RHR、training_load、ATI/CTI、tired_rate
> - 权重/体脂：**确认无字段**（手表不测 + API 无端点）
> - 官方 coroslab/COROS-MCP 是浏览器 OAuth，无头环境跑不了，故用本社区版。

## coros-mcp（备用数据获取工具）

[cygnusb/coros-mcp](https://github.com/cygnusb/coros-mcp) 是一个 MCP 服务器，通过逆向 COROS 移动端 API 提供程序化数据访问（HRV、每日指标、活动、睡眠、训练计划）。**比 Playwright 脚本更稳定，但覆盖范围不同。**

**安装位置：** `~/projects/coros-mcp/`
**虚拟环境：** `~/projects/coros-mcp/.venv/`
**编译（如果重装 Go 工具）：** 源码含 replace 指令，不能用 `go install`，用 `git clone && cd repo && go build -o ~/go/bin/SmartScaleConnect .`
**账号：** 同 `running_coach.py`，从环境变量 `COROS_EMAIL` / `COROS_PWD` 读取（区域 cn），勿在文件中内联明文
**认证：** 已通过 `coros-mcp auth`（内部调用）完成，token 存储在系统 keyring

### 重点 API 端点（用于逆向或手动请求）

**Web API**（`https://teamcnapi.coros.com`）：
- 活动查询：`/activity/query?size=20&pageNumber={n}&modeList=`
- 每日指标：`/analyse/dayDetail/query?startDay={Ymd}&endDay={Ymd}`
- 综合指标（含VO2max）：`/analyse/query`
- 面板：`/dashboard/query`

**Mobile API**（`https://apicn.coros.com`）：
- 睡眠：`/coros/data/statistic/daily?startDay={Ymd}&endDay={Ymd}&type=4`

**已确认不包含体重数据：** 以上所有已知 API 端点均不含体重/体脂/体成分字段。详见 `references/coros-api.md`。

### 可用工具

```bash
# 进入虚拟环境后：
coros-mcp auth-status      # 检查认证状态
coros-mcp sync --from 20260101  # 回填数据到本地 SQLite 缓存
coros-mcp cache-status     # 查看缓存覆盖范围
```

### ⚠️ cron 环境限制（2026-07-17 实测）

**`coros-mcp auth` 是交互式 CLI** — 它用 `input()` 提示输入邮箱/密码，不能在 cron 或任何非交互环境中使用。直接调用会报 `EOFError: EOF when reading a line`。

**解决办法：Python 程序化调 API**（绕过 CLI，直接在 Python 中调用 coros-mcp 的底层模块）：

```python
import sys
sys.path.insert(0, '/home/wangsiji/projects/coros-mcp')
from coros_api import login, get_activities
from datetime import datetime, timedelta

# 凭证从环境变量读取，勿在此内联明文（安全）
import os
EMAIL = os.environ["COROS_EMAIL"]
PASSWORD = os.environ["COROS_PWD"]
ok = login(EMAIL, PASSWORD, region="cn")
if ok:
    acts = get_activities(
        (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        datetime.now().strftime('%Y%m%d')
    )
```

**优先级（cron 上下文）：**
1. Playwright 脚本（`running_coach.py`）
2. 等5秒重试 Playwright
3. coros-mcp 程序化 API（如 coros_api.login() 的函数签名与 CLI 不同，先 `dir(coros_api)` 确认实际函数名和参数）
4. 缓存兜底（`~/.hermes/coros-cache/*.json`）
5. 占位数据兜底

### 与 Playwright 脚本的对比

| 维度 | Playwright（running_coach.py） | coros-mcp |
|------|-------------------------------|-----------|
| 原理 | 登录网页，拦截请求 | 直接调 API |
| 依赖 | Playwright、Chromium | httpx |
| 速度 | ~55s | ~5-10s |
| 活动数据 | ✅ 完整 | ✅ 完整 |
| 睡眠数据 | ❌ 不可用 | ✅ 有（但需验证准确性） |
| 训练计划 | ❌ | ✅ 可读/写 |
| 体重数据 | ❌ | ❌ |

---

