---
name: cron-cache-fallback
description: 无头/cron 环境下 running_coach.py 浏览器登录超时时的缓存聚合回退法（聚合 ~/.hermes/coros-cache 每日文件重建任意时间窗）
---

# Cron / 无头环境：实时同步失败 → 缓存聚合回退

> 2026-07-19 实测：cron 跑 `running_coach.py --days 7 --daily-report` 连续两次在 playwright 阶段超时
> （一次 `wait_for_url(...login...)` 60s，一次 `wait_for_load_state("networkidle")` 30s）。
> 高驰 SPA 在无头 chromium 下常不触发 networkidle，且登录偶发偏慢。
> 此时脚本的 `load_cache()` **无法**满足 7 天窗（它只匹配「当天日期命名 + 精确 date_from/date_to」的单个文件），
> 于是直接 `fetch_activities` 崩溃，而不是回退。可恢复的数据其实在每日缓存文件里。

## 缓存结构

- 目录：`~/.hermes/coros-cache/`
- 文件：`<YYYY-MM-DD>.json`（每次 running_coach.py 运行都会尝试保存，失败的窗也会写成空 activities）
- 单文件结构：
  ```json
  {"fetched_at":"2026-07-18T20:02:15", "date_from":"2026-07-12", "date_to":"2026-07-18",
   "count":N, "activities":[{ "date":"2026年7月17日", "raw_date":"20260717",
     "sport":"12k轻松跑", "dist":"12.59km", "dist_km":12.59, "duration":"01:17:46",
     "duration_sec":4666, "pace":"6'12\"", "pace_sec":372, "hr":146,
     "hr_zone":"E区", "tl":122 }]}
  ```
- 每日文件会含「当天 + 之前若干天」的活动（取决于那次运行的窗），所以聚合多个每日文件即可重建任意窗。

## 聚合脚本（重建任意窗）

```python
import json
from pathlib import Path

CACHE = Path.home() / ".hermes" / "coros-cache"
date_from, date_to = "2026-07-13", "2026-07-19"   # 目标窗
df, dt = int(date_from.replace("-","")), int(date_to.replace("-",""))

seen, acts = set(), []
for f in CACHE.glob("*.json"):
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for a in data.get("activities", []):
        rd = a.get("raw_date")
        if not rd:
            continue
        n = int(rd)
        if df <= n <= dt and rd not in seen:
            seen.add(rd)
            acts.append(a)

acts.sort(key=lambda x: x["raw_date"], reverse=True)
print(f"窗口 {date_from}~{date_to} 命中 {len(acts)} 条")
for a in acts:
    print(a["raw_date"], a["sport"], a["dist"], a["pace"], a["hr"], a["hr_zone"], "TL", a["tl"])
```

## 坑

- **「今天」可能不完整**：每日缓存只含其 `fetched_at` 之前的跑。若今日跑在最新缓存文件之后，窗里没有今日记录 → 日报「今日训练」标「未记录」，不要编造。
- **空窗文件会骗过 `load_cache`**：失败的 `--days 7` 运行也会写 `2026-07-19.json`（count=0），`load_cache` 因此返回 `[]`（falsy）→ 仍走 fetch 崩溃。所以别信 `load_cache` 对多日窗。
- **先重试一次再回退**：实时同步偶发超时，值得 `timeout 280 python3 ... --days 7 --daily-report` 重试一次；仍失败再聚合缓存。
- **聚合后照常跑日报逻辑**：本技巧只负责拿到 `activities` 列表；拿到后可直接 `import running_coach; running_coach.generate_daily_report(acts)`，或手写点评（用 daily-report-template.md 的检查清单）。
- **黄金 5 条说「不用缓存」是指优先拉最新**；无头环境实时链路不可用时的缓存回退是例外，不是违规。
