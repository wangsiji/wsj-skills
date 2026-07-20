#!/usr/bin/env python3
"""每日拉取 COROS 当日跑步+俯卧撑+体重，写入 vault 数据文件，生成日报。

修复记录（2026-07-20）：
- 原 pull_day 用 fetch_activities(auth, d, d) 传 startDay/endDay 区间，
  COROS /activity/query 对该区间参数返回 "Service exceptions"，导致永远拿到 0 条；
  改为不带日期区间拉取最近活动，再按 Asia/Shanghai 日期客户端过滤。
- 原脚本依赖 get_stored_auth() 的本地 token，但环境无持久化 token，
  get_stored_auth() 返回 None → 同样 0 条；改为读取 running_coach.py 的
  明文凭证并注入环境变量后用 try_auto_login() 登录（已验证可用，region=cn）。
- 俯卧撑行原格式错位且未解析个数/组数；改为按 "X 组 Y 个" 解析并聚合当天多组。
"""
import sys, os, re, json, asyncio, subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT = Path.home() / "projects" / "wsj-second-brain" / "01-Projects" / "Routine"
RUN_FILE = VAULT / "跑步数据.md"
PUSH_FILE = VAULT / "俯卧撑数据.md"
WEIGHT_FILE = VAULT / "体重数据.md"
SLEEP_FILE = VAULT / "睡眠数据.md"
COROS_MCP = Path.home() / "projects" / "coros-mcp"
PY = str(COROS_MCP / ".venv" / "bin" / "python")

# 上海时区（+8），不依赖 tzdata 包
SH = timezone(timedelta(hours=8))

# 凭证来源：running-coach skill 的 running_coach.py（明文，已存在，不新增）
RC = Path.home() / ".hermes" / "skills" / "custom" / "wsj-running-coach" / "scripts" / "running_coach.py"


def append_row(path: Path, row: str):
    lines = path.read_text(encoding="utf-8").split("\n")
    # 同日去重：若已有该日期行，替换而非追加
    cols = row.split("|")
    day = cols[1].strip() if len(cols) > 1 else ""
    if day:
        for i, ln in enumerate(lines):
            lcols = ln.split("|")
            if len(lcols) > 1 and lcols[1].strip() == day:
                lines[i] = row
                path.write_text("\n".join(lines), encoding="utf-8")
                return
    # 在表格第一行数据前插入（表头后第一行）
    insert_at = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("| 日期") or ln.strip().startswith("|日期"):
            insert_at = i + 2
            break
    if insert_at is None:
        lines.append(row)
    else:
        lines.insert(insert_at, row)
    path.write_text("\n".join(lines), encoding="utf-8")


def pull_day(target_date: str):
    """拉取 target_date(Asia/Shanghai) 的 COROS 跑步+俯卧撑活动。

    返回 (acts_list, err)。arts_list 为 dict 列表。
    说明：COROS /activity/query 的 startDay/endDay 区间参数会触发 'Service exceptions'，
    因此这里不带日期区间，改为拉取最近活动后在客户端按日期过滤。
    """
    src = RC.read_text(encoding="utf-8")
    EMAIL = re.search(r'EMAIL\s*=\s*"([^"]+)"', src).group(1)
    PASSWORD = re.search(r'PASSWORD\s*=\s*"([^"]+)"', src).group(1)
    os.environ.setdefault("COROS_EMAIL", EMAIL)
    os.environ.setdefault("COROS_PASSWORD", PASSWORD)
    os.environ.setdefault("COROS_REGION", "cn")

    script = f'''
import sys, asyncio, json, traceback
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "{COROS_MCP}")
from coros_api import try_auto_login, _base_url, _auth_headers, ENDPOINTS, fetch_activity_detail
SH = timezone(timedelta(hours=8))
TARGET = "{target_date}"
RUN_MODES = [100, 102, 103]
STR_MODE = 402

HR_ZONE_NAMES = ["E", "M", "HV", "VO2", "A", "I"]  # zoneIndex 0..5（按 COROS 心率区间）

def _zone_str(zone_list, want_type):
    """从 zoneList 提取指定 type 的区间百分比分布字符串，如 'E28% M71%'。"""
    for z in zone_list or []:
        if z.get("type") == want_type:
            items = sorted(z.get("zoneItemList", []), key=lambda x: x.get("zoneIndex", 0))
            parts = []
            for it in items:
                idx = it.get("zoneIndex", 0)
                pct = it.get("percent", 0)
                if pct <= 0:
                    continue
                name = HR_ZONE_NAMES[idx] if want_type == 126 and idx < len(HR_ZONE_NAMES) else str(idx)
                parts.append(f"{name}{pct}%")
            return " ".join(parts)
    return ""

async def main():
    try:
        auth = await try_auto_login()
        if not auth:
            print("[]"); return
        out = []
        for mode in RUN_MODES + [STR_MODE]:
            params = {{"pageNumber": 1, "size": 100, "modeList": str(mode)}}
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(_base_url(auth.region) + ENDPOINTS["activity_list"],
                                params=params, headers=_auth_headers(auth))
            for it in r.json().get("data", {{}}).get("dataList", []):
                ts = it.get("startTime")
                if not ts:
                    continue
                day = datetime.fromtimestamp(int(ts), SH).strftime("%Y-%m-%d")
                if day != TARGET:
                    continue
                aid = it.get("labelId") or it.get("activityId")
                st = it.get("sportType") or it.get("sport_type") or 100
                rec = {{
                    "name": it.get("name") or it.get("remark"),
                    "sport_type": st,
                    "dist_m": it.get("distance") or 0,
                    "hr": it.get("avgHr"),
                    "tl": it.get("trainingLoad"),
                    "dur_s": it.get("totalTime"),
                }}
                try:
                    det = await fetch_activity_detail(auth, aid, st)
                    s = det.get("summary", {{}}) or {{}}
                    start_ts = s.get("startTimestamp") or ts
                    rec["start_time"] = datetime.fromtimestamp(int(start_ts), SH).strftime("%H:%M") if start_ts else ""
                    dur_ms = s.get("totalTime") or it.get("totalTime") or 0
                    rec["dur_s"] = int(dur_ms) // 1000 if dur_ms > 1000 else (dur_ms or 0)
                    dist_m = s.get("distance") or it.get("distance") or 0
                    dist_m = dist_m / 100.0 if dist_m > 1000 else dist_m
                    rec["dist_m"] = dist_m
                    if rec["dur_s"] and dist_m:
                        spm = rec["dur_s"] / dist_m * 1000.0
                        m = int(spm // 60); sec = int(spm % 60)
                        rec["pace"] = f"{m}:{sec:02d}"
                    else:
                        rec["pace"] = ""
                    rec["hr"] = s.get("avgHr") or it.get("avgHr")
                    rec["tl"] = s.get("trainingLoad") or it.get("trainingLoad")
                    zl = det.get("zoneList", [])
                    rec["hr_zones"] = _zone_str(zl, 126)
                    rec["pace_zones"] = _zone_str(zl, 130)
                except Exception:
                    rec["start_time"] = ""
                    rec["pace"] = ""
                    rec["hr_zones"] = ""
                    rec["pace_zones"] = ""
                out.append(rec)
        print(json.dumps(out, ensure_ascii=False))
    except Exception:
        traceback.print_exc()
        print("[]")

asyncio.run(main())
'''
    r = subprocess.run([PY, "-c", script], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        return None, r.stderr[-500:]
    out = r.stdout.strip()
    if not out:
        return [], ""
    try:
        return json.loads(out.splitlines()[-1]), ""
    except Exception:
        # 重试一次（COROS 网络偶发空响应）
        r2 = subprocess.run([PY, "-c", script], capture_output=True, text=True, timeout=180)
        if r2.returncode == 0 and r2.stdout.strip():
            try:
                return json.loads(r2.stdout.strip().splitlines()[-1]), ""
            except Exception:
                pass
        return None, f"解析失败: {out[-300:]}"


def pull_sleep(target_date: str):
    """拉取 target_date(Asia/Shanghai) 的 COROS 睡眠数据（含昨夜）。"""
    src = RC.read_text(encoding="utf-8")
    EMAIL = re.search(r'EMAIL\s*=\s*"([^"]+)"', src).group(1)
    PASSWORD = re.search(r'PASSWORD\s*=\s*"([^"]+)"', src).group(1)
    os.environ.setdefault("COROS_EMAIL", EMAIL)
    os.environ.setdefault("COROS_PASSWORD", PASSWORD)
    os.environ.setdefault("COROS_REGION", "cn")
    d = datetime.strptime(target_date, "%Y-%m-%d")
    prev = (d - timedelta(days=1)).strftime("%Y-%m-%d")
    d_y = d.strftime("%Y%m%d")
    prev_y = prev.replace("-", "")
    script = f'''
import sys, asyncio, json, traceback
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "{COROS_MCP}")
from coros_api import try_auto_login, login_mobile, fetch_sleep
SH = timezone(timedelta(hours=8))
TARGET = "{target_date}"
EMAIL = "{EMAIL}"
PASSWORD = "{PASSWORD}"
REGION = "cn"
async def main():
    try:
        # 优先 web token（跑步/体重用）；睡眠必须 mobile token，
        # try_auto_login 偶发失败，失败也继续用 login_mobile 兜底
        auth = await try_auto_login()
        try:
            auth = await login_mobile(EMAIL, PASSWORD, REGION)
        except Exception:
            if not auth:
                print("null"); return
        if not auth:
            print("null"); return
        recs = await fetch_sleep(auth, "{prev_y}", "{d_y}")
        # 返回所有匹配记录（按各自 happenDay=醒来日 落对应日期行）
        out = []
        for r in recs:
            sd = r.phases
            out.append({{"date": r.date, "total": r.total_duration_minutes,
                "deep": sd.deep_minutes if sd else None,
                "light": sd.light_minutes if sd else None,
                "rem": sd.rem_minutes if sd else None,
                "awake": sd.awake_minutes if sd else None,
                "avg_hr": r.avg_hr, "min_hr": r.min_hr,
                "max_hr": r.max_hr, "quality": r.quality_score}})
        print(json.dumps(out, ensure_ascii=False))
    except Exception:
        traceback.print_exc()
        print("null")
asyncio.run(main())
'''
    r = subprocess.run([PY, "-c", script], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        return None, r.stderr[-500:]
    out = r.stdout.strip()
    if not out or out == "null":
        return None, ""
    try:
        return json.loads(out.splitlines()[-1]), ""
    except Exception as e:
        return None, f"解析失败: {out[-300:]}"


def main():
    day_str = datetime.now(SH).strftime("%Y-%m-%d")
    acts, err = pull_day(day_str)
    if acts is None:
        print(f"❌ 跑步/俯卧撑拉取失败: {err}")
        acts = []
    run_rows, push_rows = [], []
    push_reps_total = 0
    push_sets_total = 0
    push_names = []
    for a in acts:
        name = a.get("name") or ""
        sport = (a.get("sport_name") or "").lower()
        dist = (a.get("dist_m") or 0) / 1000.0
        hr = a.get("hr") or ""
        tl = a.get("tl") or ""
        st = a.get("sport_type")
        is_run = ("跑" in name or "run" in sport or st in (100, 102, 103))
        if is_run and dist > 0:
            dur_s = a.get("dur_s") or 0
            dur = f"{dur_s//60}:{dur_s%60:02d}" if dur_s else ""
            pace = a.get("pace") or ""
            hrz = a.get("hr_zones") or ""
            run_rows.append(f"| {day_str} | {a.get('start_time','')} | {dist:.1f} | {dur} | {pace} | {hr} | {hrz} | {tl} | 自动(COROS) | {name} |")
        elif "俯卧撑" in name:
            m = re.search(r"(\d+)\s*组\s*(\d+)\s*个", name)
            sets = int(m.group(1)) if m else 1
            reps_per_set = int(m.group(2)) if m else 0
            # "4组12个" = 4 组 × 12 个/组 = 48 个（总个数 = 组数 × 每组个数）
            push_reps_total += sets * reps_per_set
            push_sets_total += sets
            push_names.append(name)

    if push_reps_total > 0:
        if len(set(push_names)) == 1:
            note = f"{push_names[0]} ×{len(push_names)}"
        else:
            note = "；".join(push_names)
        push_rows.append(f"| {day_str} | {push_reps_total} | {push_sets_total} | 标准 | 自动(COROS) | {note} |")

    for row in run_rows:
        append_row(RUN_FILE, row)
    for row in push_rows:
        append_row(PUSH_FILE, row)

    # 体重（官方 MCP queryUserInfo）
    weight_rows = []
    try:
        wr = subprocess.run([PY, "-c",
            f"import sys,asyncio;sys.path.insert(0,'{COROS_MCP}');"
            "from coros_weight import get_weight_kg;"
            "print(asyncio.run(get_weight_kg()) or '')",
            ], capture_output=True, text=True, timeout=90)
        wk = wr.stdout.strip()
        if wk and wk.replace('.', '').isdigit():
            jin = float(wk) * 2
            weight_rows.append(f"| {day_str} | {jin:.1f} | 自动(COROS·queryUserInfo) |")
            append_row(WEIGHT_FILE, weight_rows[0])
    except Exception as e:
        print(f"⚠️ 体重拉取失败: {e}")

    # 睡眠（非官方 mobile API fetch_sleep）—— 每条按其 happenDay(醒来日) 落对应日期行
    sleep_rows = []
    try:
        sl_list, sl_err = pull_sleep(day_str)
        if sl_list:
            for sl in sl_list:
                rec_date = sl.get("date")  # YYYYMMDD 醒来日
                if not rec_date:
                    continue
                rec_day = f"{rec_date[:4]}-{rec_date[4:6]}-{rec_date[6:8]}"  # YYYY-MM-DD
                total = sl.get("total") or 0
                deep = sl.get("deep") or 0
                light = sl.get("light") or 0
                rem = sl.get("rem") or 0
                awake = sl.get("awake") or 0
                avg_hr = sl.get("avg_hr") or ""
                quality = sl.get("quality")
                q = quality if quality and quality != -1 else ""
                row = f"| {rec_day} | {total} | {deep} | {light} | {rem} | {awake} | {avg_hr} | {q} | 自动(COROS) |"
                append_row(SLEEP_FILE, row)
                sleep_rows.append(row)
        elif sl_err:
            print(f"⚠️ 睡眠拉取失败: {sl_err}")
    except Exception as e:
        print(f"⚠️ 睡眠拉取异常: {e}")

    # 日报
    print(f"🏃 每日训练同步 | {day_str}")
    print("━" * 30)
    for r in run_rows:
        print("跑步:", r)
    for r in push_rows:
        print("俯卧撑:", r)
    for r in weight_rows:
        print("体重:", r)
    for r in sleep_rows:
        print("睡眠:", r)
    if not run_rows and not push_rows and not weight_rows and not sleep_rows:
        print("今日无新活动记录（休息日或手表未同步）")


if __name__ == "__main__":
    main()
