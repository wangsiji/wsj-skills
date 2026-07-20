# COROS API Field Quirks & Workarounds

Compiled from real-time debugging during cron development (2026-07-20). All values are from the **China (cn/teamcnapi.coros.com)** endpoint unless noted.

## Timestamp Formats

| Field | API Source | Unit | Notes |
|-------|-----------|------|-------|
| `startTime` | activity list `GET /activity/query` | **seconds** (Unix epoch UTC) | Safe for `datetime.fromtimestamp(ts, tz)` |
| `startTimestamp` | activity detail `POST .../activity/detail` → `summary` | **milliseconds** (Unix epoch × 1000) | **NOT seconds!** `fromtimestamp(ms, tz)` → year 7624 → broken. Use `startTime` from activity list instead. |
| `totalTime` | activity detail → `summary` | **centiseconds** (1/100 s) | Convert: `int(val) // 100`. Activity list's `totalTime` is **seconds**. The `or` chain picks detail value first since both are non-falsy → must use `// 100` not `// 1000`. |

## Zone Lists (`zoneList[]`)

Returned by `fetch_activity_detail()`. Each entry has `type` + `zoneItemList[]` with `zoneIndex/percent/leftScope/rightScope/second`.

| Type | Meaning | Zone Names | Example |
|------|---------|------------|---------|
| 126 | **Heart Rate zones** | `E(0)`, `M(1)`, `HV(2)`, `VO2(3)`, `A(4)`, `I(5)` | `E 28% M 71% HV 1%` |
| 130 | **Pace zones** | `Z0`, `Z1`, `Z2`, `Z3` (unlabeled, use index prefix) | `Z0 95% Z1 3% Z2 2%` |

`leftScope`/`rightScope` for type 126 = heart rate in bpm; for type 130 = pace in some scale (not needed for display—use percent only). Zone 5 (I) rightScope is 434+ (cap).

## Distance

`summary.distance` is in **centimeters** (e.g. 600339 cm = 6003 m = 6.0 km). Activity list `it.get("distance")` appears to be in | centimeters too.

Convert: `dist_m / 100.0` to meters, then `/ 1000` to km.

## Activity vs Detail Differences

| Attribute | `activity_list` (`it.get`) | `fetch_activity_detail` (`s.get`) | Prefer |
|-----------|---------------------------|-----------------------------------|--------|
| `startTime`/`startTimestamp` | seconds (UTC) | milliseconds (UTC×1000) | list |
| `totalTime` | seconds | centiseconds `// 100` | detail (richer), but unit conversion needed |
| `distance` | cm | cm (same) | detail |
| `avgHr` | available | in summary, more reliable | detail |
| `trainingLoad` | available | in summary | detail |
| `zoneList` | **not available** | ✅ available | detail only |
| `lapList`/`lapGraphList` | **not available** | ✅ available | detail only |

**Best practice**: use activity list for `startTime` (timestamp) and date filtering; use `fetch_activity_detail` for duration, distance, HR, zones. Merge with try/except — detail call can fail (network timeout) but list call already succeeded.

## Sleep API

- `fetch_sleep(auth, startDay, endDay)` uses **mobile API** (not web) → needs `mobile_access_token`. Call `login_mobile()` explicitly before `fetch_sleep()`; `try_auto_login()` explicitly skips mobile login.
- `SleepRecord.date` = `happenDay` = **YYYYMMDD** (no hyphens). It's the **wake-up day** (not sleep-onset day).
- Mobile API returns HTTP 500 intermittently on refresh — retry 3× with 2s delay.
- Date range format for mobile API: `YYYYMMDD` strings (not `YYYY-MM-DD`).

## Subprocess F-String Nesting Trap

When building subprocess scripts via outer f-string:
```python
script = f'''...  # outer f-string processes ALL {expressions}
    rec = f"{name}"  # INNER f-string: {name} is evaluated by OUTER f-string → NameError
'''
```
**Fix**: inside the template string, never use nested `f"..."`. Use string concatenation: `name + str(pct) + "%"`, or `.format()` with doubled braces (risky). This affects all `{...}` expressions inside the inner script strings.
