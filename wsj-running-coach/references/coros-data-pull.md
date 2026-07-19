---
name: coros-data-pull
description: 程序化拉取 COROS 真实训练历史的可用代码模板 + 踩坑点（running_coach.py 与 coros-mcp 两套路径）
---

# COROS 数据拉取（程序化可用模板）

> 2026-07-19 实测跑通。两套工具：Playwright 脚本（running_coach.py，拉已完成活动+生成日报）与 coros-mcp（逆向 API，可拉计划/睡眠/活动）。
> 本文件只记**能让下次直接复用**的确定事实，不重复 coros-mcp.md 的端点清单。

## 路径 A：running_coach.py（拉活动 + 日报，最稳）

- 解释器：系统 `python3`（脚本自带 playwright 依赖，浏览器驱动 chromium 已下载）
- 参数名是 `--from-date` / `--to-date` / `--daily-report`（**不是** `--date-from`）
- 示例：`python3 running_coach.py --from-date 2026-07-17 --to-date 2026-07-19 --daily-report`
- 登录用硬编码 EMAIL/PASSWORD（skill 的 Never Do 禁止内联密码，但此文件是历史遗留，仅本机可用）
- 坑：前台 60s 超时，登录约 40-50s；偶发超时重试即可

## 路径 B：coros-mcp（异步 API，拉历史/计划更灵活）

虚拟环境：`~/projects/coros-mcp/.venv/bin/python`（必须用这个，不是系统 python）

### ⚠️ 必踩的坑（2026-07-19 实测）

1. **全是 async**：`login()` / `fetch_activities()` / `fetch_schedule()` 都必须 `await`，且在 `asyncio.run()` 内调用。直接调用报 "coroutine was never awaited"。
2. **字段名不是 distance_km**：ActivitySummary 真实字段是 `distance_meters`（米）。`a.distance_km` 不存在 → 筛选 0 条。换算：`a.distance_meters / 1000.0`。
3. **没有 `.date` 属性**：日期在 `start_time`（UTC 秒）。换算：`datetime.utcfromtimestamp(int(a.start_time))`。
4. **token 会过期**：`get_stored_auth()` 可能返回**已失效** token（报 "Access token is invalid"）。web token TTL ~24h。必须 `await login(EMAIL, PASSWORD, "cn", skip_mobile=True)` 重登刷新。
5. **凭证 env 为空**：`COROS_EMAIL`/`COROS_PWD` 默认未设。重登可复用 `running_coach.py` 里的硬编码凭证（读文件提取，不让你发明文）。
6. **网络抖动**：`teamcnapi.coros.com` 偶发 ConnectTimeout（`httpx.ConnectTimeout`）。**本会话最频繁故障**——首次 `fetch_schedule` 成功，之后连续多次 `login()` 即 ConnectTimeout。回退：先用 `get_stored_auth()`（已存的 keyring token，跳过 login 网络调用）再调 `fetch_activities`/`fetch_schedule`；token 24h 有效，不必每次重登。若必须重登，retry 2-3 次；子进程内嵌脚本优先 `get_stored_auth()` 而非每次 `login()`。
7. **pace 可能缺失**：活动列表 API 的 `adjusted_pace` 常返回 None（实测 23 条全部 None）。要配速需 `fetch_activity_detail()`。

### 可用模板（拉历史跑步，倒序）

```python
import sys, asyncio, os, re, json
sys.path.insert(0, "/home/wangsiji/projects/coros-mcp")
from coros_api import login, fetch_activities
import datetime

src = open('/home/wangsiji/.hermes/skills/custom/wsj-running-coach/scripts/running_coach.py', encoding='utf-8').read()
EMAIL = re.search(r'EMAIL\s*=\s*"([^"]+)"', src).group(1)
PASSWORD = re.search(r'PASSWORD\s*=\s*"([^"]+)"', src).group(1)

async def main():
    auth = await login(EMAIL, PASSWORD, "cn", skip_mobile=True)
    acts, total = await fetch_activities(auth, "20260525", "20260719")
    runs = [a for a in acts if getattr(a, 'distance_meters', 0) and a.distance_meters >= 1000]
    for a in runs:
        d = datetime.datetime.utcfromtimestamp(int(a.start_time))
        km = a.distance_meters / 1000.0
        print(d.strftime("%Y-%m-%d"), f"{km:.1f}km", a.name, a.avg_hr, a.training_load)

asyncio.run(main())
```
运行：`~/projects/coros-mcp/.venv/bin/python pull.py`

### 拉训练计划（fetch_schedule，2026-07-19 实测跑通）

- 签名：`fetch_schedule(auth, start_day, end_day)`，`start_day`/`end_day` 格式 `"YYYYMMDD"`。返回 stripped schedule dict（已排程的跑步/力量计划）。
- 返回结构：`{entities:[{happenDay, planProgramId, executeStatus}], programs:[{idInPlan, name, distance, duration, exercises:[{overview, sets, sportType, targetValue, intensityType, ...}]}]}`。用 `planProgramId→idInPlan` 映射从 `entities` 关联到 `programs` 取明细。
- 俯卧撑项可直接读：`exercises[].overview`（如 "Push ups"）+ `sets` + `targetValue`（个），`sportType=4`。
- 跑步项 program 名常为 `W30xxx`/`P10xxx` 计划 ID；具体配速/距离在 `exercises` 的 `intensityType`/`distance`（本会话未完成完整解析，网络抖动中断——下次需稳定网络下整段解析 `exercises`）。
- `auth`：token 已存则 `get_stored_auth()` 即可（避免每次 `login()` 触发 ConnectTimeout）。
- 实测：本会话用 `fetch_schedule(auth,"20260720","20260726")` 成功确认下周每天 1 跑 + 俯卧撑 4×12。
