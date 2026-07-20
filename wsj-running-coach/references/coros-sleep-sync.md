---
name: COROS 睡眠同步（fetch_sleep）
description: cron 每日拉取 COROS 睡眠数据的实现细节、踩坑与字段映射
---

## 数据源
- `coros-mcp/coros_api.fetch_sleep(auth, start_day, end_day)` → `list[SleepRecord]`
- 走 **mobile API**（`apieu.coros.com/coros/data/statistic/daily`，`statisticType=1`），非 Training Hub web API
- **`SleepRecord.date`（= `happenDay`）是「醒来日」，不是入睡日**。`fetch_sleep(start=prev_y, end=d_y)` 返回区间内**每天一条**（prev 夜醒来 + target 夜醒来各一条）。**每条必须按其自身 `date` 落对应日期行，绝不可统一写进 `day_str` 行**——实测踩过数据错位 bug（见踩坑 5）。
- `SleepRecord` 字段：`date`(YYYYMMDD 无横杠) / `total_duration_minutes` / `phases{deep,light,rem,awake,nap}_minutes` / `avg_hr` / `min_hr` / `max_hr` / `quality_score`(-1=未计算)

## 关键踩坑（实测）
1. **mobile token 必须显式获取**：`try_auto_login()` 文档明确「Always skips mobile login」——只返回 web token。直接 `fetch_sleep(auth,...)` 会触发 `_ensure_mobile_token(auth)` → `auth.mobile_access_token` 报 `NoneType` 错误。
   修正：调用前 `auth = await login_mobile(email, password, "cn")`。web 登录偶发失败时 mobile 登录仍稳，可作兜底——cron 脚本逻辑：`try_auto_login()` 后无条件 `try: login_mobile(...)`，`except` 时仅当 auth 也为 None 才放弃。
2. **日期格式不匹配（静默丢数据）**：`SleepRecord.date` 是 `YYYYMMDD`（如 `20260720`），目标日是 `YYYY-MM-DD`。**转换：`rec_day = f"{date[:4]}-{date[4:6]}-{date[6:8]}"`**，用自己的 `date` 生成落行日期，不要和 `day_str`/`prev` 比对是否相等（否则只落一条、漏其余日期）。`prev_y` 用 `prev.replace("-","")` 生成，不要对字符串再 `.strftime`。
3. **质量分 -1**：COROS 未计算时 `quality_score=-1`，写入数据表**留空**（不写 -1）。
4. **`prev.strftime` 二次调用**：`prev` 已是 `strftime` 返回的字符串，再 `.strftime` 报 `'str' object has no attribute 'strftime'`。字符串转 YYYYMMDD 用 `.replace("-","")`。
5. **⚠️ 醒来日错位（用户实测抓出）**：`happenDay` 是**醒来那天**，不是入睡那天。例：7/19 醒来=463min、7/20 醒来=383min 是两条独立记录（各落 7-19 / 7-20 行）。**错误写法**：只取 `recs` 第一条（`break`）并写进 `day_str` 行 → 把 7/19 的 463 误写进 7/20 行，且漏写 7/19。**正确写法**：遍历所有 `recs`，每条用自身 `r.date` 生成 `rec_day` 调 `append_row(SLEEP_FILE, row)`（同日去重已保证重跑幂等）。区间拉 `prev_y..d_y` 即可覆盖昨夜+今夜，无需更长区间。

## 字段映射 → 睡眠数据.md
| 数据表列 | SleepRecord 字段 |
|---------|-----------------|
| 总时长(min) | total_duration_minutes |
| 深睡 | phases.deep_minutes |
| 浅睡 | phases.light_minutes |
| REM | phases.rem_minutes |
| 清醒 | phases.awake_minutes |
| 睡眠心率 | avg_hr |
| 质量分 | quality_score（= -1 时留空）|

## 落地
- 数据文件：`01-Projects/Routine/睡眠数据.md`（category `[[24-休闲]]`；原则层在 `02-Areas/13-睡眠.md`，已在末尾加 `[[睡眠数据]]` 链接；**勿**在 `10-健康.md` 仪表盘再加重复睡眠行，已有 `13-睡眠` 行）
- cron：已并入 `~/.hermes/scripts/_cron_sync_coros.py`（job `818beb975a1f`，每天 10:00），与跑步/俯卧撑/体重同批，`append_row` 同日去重
- 实测 2026-07-20：463min / 深58 浅272 REM133 清醒40 / 心率55
