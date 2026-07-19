---
name: coros-pull-history
description: 用 coros-mcp 拉取历史训练活动/排程的可用代码模式（字段名、async、token 刷新）
---

# 拉 COROS 历史训练数据（实测可用）

## 凭证与 token
- `running_coach.py`（wsj-running-coach/scripts）里硬编码了 `EMAIL`/`PASSWORD`，可直接复用重登，不让用户发明文。
- token TTL ~24h，过期后 `fetch_*` 报 "Access token is invalid"。刷新：
  ```python
  auth = await login(EMAIL, PASSWORD, "cn", skip_mobile=True)
  ```
- 区域用 `cn` → `teamcnapi.coros.com`。login 成功但 fetch 偶尔 ConnectTimeout，retry 2-3 次即可。

## 关键字段（与直觉不同，易踩坑）
- `ActivitySummary.distance_meters`（不是 `distance_km`）
- 日期在 `start_time`（UTC Unix 秒），不是 `date`；用 `datetime.utcfromtimestamp(int(start_time))`
- `login` / `fetch_activities` / `fetch_schedule` 都是 **async**，必须 `await`
- `fetch_activities(auth, start_day, end_day)` 返回 `(activities, total_count)` 元组
- `fetch_schedule(auth, start_day, end_day)` 拉手表排程（训练计划）

## 最小可用片段

```python
import sys, asyncio, re, json
sys.path.insert(0, "/home/wangsiji/projects/coros-mcp")
from coros_api import login, fetch_activities
import datetime as _dt

src = open("/home/wangsiji/.hermes/skills/custom/wsj-running-coach/scripts/running_coach.py", encoding="utf-8").read()
EMAIL = re.search(r'EMAIL\s*=\s*"([^"]+)"', src).group(1)
PASSWORD = re.search(r'PASSWORD\s*=\s*"([^"]+)"', src).group(1)

async def main():
    auth = await login(EMAIL, PASSWORD, "cn", skip_mobile=True)
    acts, total = await fetch_activities(auth, "20260525", "20260719")
    runs = [a for a in acts if (a.distance_meters or 0) >= 1000]
    for a in runs:
        d = _dt.datetime.utcfromtimestamp(int(a.start_time))
        print(d.strftime("%Y-%m-%d"), f"{(a.distance_meters or 0)/1000:.1f}km", a.name, "hr=", a.avg_hr)
asyncio.run(main())
```

## 用法（倒推训练规划）
- 拉过去 8~12 周活动，按周聚合跑量/次数/TL，看心率区分布（判断 E/T/I 占比），对照 VDOT 与破三配速缺口。
- 真实基线示例（用户 2026-05-30~07-16）：23 次跑步全在 Z2/E 区（127-153bpm），**0 节强度课**——破三最大缺口是缺 T/I 课，不是缺量。
