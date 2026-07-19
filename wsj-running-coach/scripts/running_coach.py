#!/usr/bin/env python3
"""
Running Coach — 统一数据获取脚本
整合 coros-activity-fetch + coros-watch-data + marathon-coach 的数据获取逻辑
"""
import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

# ─── 配置 ───
EMAIL = "wangsiji@buaa.edu.cn"
PASSWORD = "1993wang123704"
LOGIN_URL = "https://training.coros.com"

CACHE_DIR = Path.home() / ".hermes" / "coros-cache"

# 心率区 (LTHR=171) — COROS Z2-Z5+ 映射
# Z2(有氧耐力)=137-154=E区,  Z3(灰色)=155-162,  Z4(乳酸阈)=163-174=T区,  Z5+(速度耐力)=175+=I区
HR_ZONES = [
    (0, 137, "Z1恢复"),
    (137, 155, "E区"),    # Z2
    (155, 163, "灰色区"),  # Z3
    (163, 175, "T区"),    # Z4
    (175, 999, "I区"),    # Z5+
]

# ─── 工具函数 ───

def hr_zone(bpm: int) -> str:
    for lo, hi, name in HR_ZONES:
        if bpm < hi:
            return name
    return "I区"


def format_pace(sec: int) -> str:
    if not sec or sec <= 0:
        return "-"
    return f"{sec // 60}'{sec % 60:02d}\""


def format_duration(sec: int) -> str:
    if not sec:
        return ""
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fetch_activities(date_from: str, date_to: str, headless: bool = True) -> list:
    """
    核心方案：
    1. Playwright 登录 COROS
    2. 拦截请求捕获 accesstoken
    3. 在 page.evaluate 里用捕获的 token 调 API 获取全量数据
    4. 直接解析 JSON，不碰 DOM
    """
    captured_token = {}

    def handle_request(request):
        if "activity/query" in request.url:
            captured_token["token"] = request.headers.get("accesstoken", "")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("request", handle_request)

        # 1. 登录
        page.goto(LOGIN_URL)
        page.wait_for_load_state("networkidle")
        page.get_by_text("Log in with Email").click()
        page.wait_for_timeout(500)
        page.locator('input[type="text"]').first.fill(EMAIL)
        page.locator('input[type="password"]').fill(PASSWORD)
        page.get_by_text("I have read and agree to the COROS Privacy Policy").click()
        page.get_by_role("button", name="Login").click()
        # ⚠️ COROS login 页面 URL 含 dash-board：https://training.coros.com/login?lastUrl=%2Fadmin%2Fviews%2Fdash-board
        #   wait_for_url("**/dash-board**") 会立即匹配，导致未登录就继续！
        #   正确方式：等 URL 离开 login 页面
        page.wait_for_url(lambda url: "login" not in url, timeout=60000)
        page.wait_for_timeout(1000)
        print("[OK] 登录成功", file=sys.stderr)

        # 2. 触发一次 API 调用以捕获 token
        page.goto("https://trainingcn.coros.com/admin/views/activities")
        page.wait_for_load_state("networkidle")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        if not captured_token.get("token"):
            print("[ERROR] 未捕获到 API token", file=sys.stderr)
            browser.close()
            return []

        token = captured_token["token"]
        print(f"[OK] Token: {token[:20]}...", file=sys.stderr)

        # 3. 在 page.evaluate 里调 API 获取全量数据
        all_items = page.evaluate(f"""
            async () => {{
                const token = "{token}";
                const all = [];
                for (let pageNum = 1; pageNum <= 20; pageNum++) {{
                    const resp = await fetch(
                        `https://teamcnapi.coros.com/activity/query?size=20&pageNumber=${{pageNum}}&modeList=`,
                        {{
                            headers: {{
                                'accept': 'application/json, text/plain, */*',
                                'accesstoken': token,
                                'referer': 'https://trainingcn.coros.com/',
                                'origin': 'https://trainingcn.coros.com'
                            }}
                        }}
                    );
                    if (!resp.ok) break;
                    const data = await resp.json();
                    const items = data?.data?.dataList || [];
                    all.push(...items);
                    if (items.length < 20) break;
                }}
                return all;
            }}
        """)

        print(f"[OK] 获取到 {len(all_items)} 条活动记录", file=sys.stderr)
        browser.close()
        raw_activities = all_items

    # ─── 解析数据 ───
    from_dt = int(date_from.replace("-", ""))
    to_dt = int(date_to.replace("-", ""))

    activities = []
    for item in raw_activities:
        date_val = item.get("date")
        if not date_val:
            continue

        date_str = str(date_val)
        if len(date_str) == 8:
            y, m, d = date_str[:4], date_str[4:6], date_str[6:8]
            date_display = f"{y}年{int(m)}月{int(d)}日"
            date_num = int(date_str)
        else:
            continue

        if not (from_dt <= date_num <= to_dt):
            continue

        dist_m = item.get("distance", 0) or 0
        dist_km = dist_m / 1000.0
        pace_sec = item.get("adjustedPace", 0) or 0
        avg_hr = item.get("avgHr", 0) or 0
        total_time = item.get("totalTime", 0) or 0
        tl = item.get("trainingLoad", 0) or 0
        name = item.get("name", "") or "跑步"
        sport_type = item.get("sportType", 0)

        activities.append({
            "date": date_display,
            "raw_date": date_str,
            "sport": name,
            "sport_type": sport_type,
            "dist": f"{dist_km:.2f}km",
            "dist_km": round(dist_km, 2),
            "duration": format_duration(total_time),
            "duration_sec": total_time,
            "pace": format_pace(pace_sec),
            "pace_sec": pace_sec if pace_sec > 0 else None,
            "hr": avg_hr if avg_hr > 0 else None,
            "hr_zone": hr_zone(avg_hr) if avg_hr > 0 else "",
            "tl": tl if tl > 0 else 0,
        })

    # 按日期降序排列
    activities.sort(key=lambda x: x.get("raw_date", ""), reverse=True)
    return activities


def save_cache(data: dict):
    """保存到本地缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = CACHE_DIR / f"{date_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache(date_from: str, date_to: str) -> list:
    """尝试从缓存加载数据"""
    cache_path = CACHE_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, encoding="utf-8") as f:
            cached = json.load(f)
        if (cached.get("date_from") == date_from and
                cached.get("date_to") == date_to):
            return cached.get("activities", [])
    except Exception:
        pass
    return None


def weekly_stats(activities: list) -> dict:
    """计算本周累计"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # 周一
    week_start_str = week_start.strftime("%Y%m%d")

    week_runs = [a for a in activities if a.get("raw_date", "") >= week_start_str]
    total_dist = sum(a.get("dist_km", 0) for a in week_runs)
    total_tl = sum(a.get("tl", 0) for a in week_runs)
    return {
        "count": len(week_runs),
        "dist_km": round(total_dist, 1),
        "total_tl": total_tl,
        "week_start": week_start.strftime("%m/%d"),
    }


def compare_with_last_week(today_activity: dict, activities: list) -> dict:
    """与上周同期对比"""
    if not today_activity:
        return {}
    raw_date = today_activity.get("raw_date", "")
    if not raw_date or len(raw_date) != 8:
        return {}
    try:
        today_date = datetime.strptime(raw_date, "%Y%m%d")
    except ValueError:
        return {}
    last_week_date = today_date - timedelta(days=7)
    last_week_str = last_week_date.strftime("%Y%m%d")

    last_week = next((a for a in activities if a.get("raw_date") == last_week_str), None)
    if not last_week:
        return {}

    dist_diff = today_activity.get("dist_km", 0) - last_week.get("dist_km", 0)
    pace_diff = None
    if today_activity.get("pace_sec") and last_week.get("pace_sec"):
        pace_diff = today_activity["pace_sec"] - last_week["pace_sec"]

    return {
        "last_week_dist": last_week.get("dist_km", 0),
        "last_week_pace": last_week.get("pace", "-"),
        "dist_diff_km": round(dist_diff, 1),
        "pace_diff_sec": pace_diff,
    }


# ─── 教练逻辑 ───

def get_milestone_info(date_str: str = None) -> dict:
    """
    根据当前日期返回所处里程碑信息
    date_str: YYYYMMDD 格式
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    y = int(date_str[:4])
    m = int(date_str[4:6])

    milestones = [
        {"name": "里程碑1：10km基准测试", "deadline": f"{y}年5月31日", "target": "< 48'00\"", "status": "进行中"},
        {"name": "里程碑2：12km阈值测试", "deadline": f"{y}年7月31日", "target": "< 4'50\"/km", "status": "进行中"},
        {"name": "里程碑3：半马比赛", "deadline": f"{y}年8月31日", "target": "< 1:38'00\"", "status": "进行中"},
        {"name": "里程碑4：30km@4'15\"模拟", "deadline": f"{y}年10月20日", "target": "掉速 ≤ 12秒/km", "status": "进行中"},
        {"name": "里程碑5：赛前30km模拟", "deadline": f"{y}年11月30日", "target": "掉速 < 15秒/km", "status": "进行中"},
    ]

    # 判断当前所处阶段
    if m < 6:
        current = milestones[0]
    elif m < 8:
        current = milestones[1]
    elif m < 9:
        current = milestones[2]
    elif m < 10:
        current = milestones[3]
    else:
        current = milestones[4]

    return current


def next_day_suggestion(today_activity: dict, all_activities: list) -> tuple:
    """
    根据今日训练类型 + 48h规则给出明日建议
    返回 (weekday_cn, training_type, description)
    """
    WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    sport = today_activity.get("sport", "").lower() if today_activity else ""
    dist_km = today_activity.get("dist_km", 0) if today_activity else 0
    hr_zone = today_activity.get("hr_zone", "") if today_activity else ""
    pace_sec = today_activity.get("pace_sec") if today_activity else None

    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_weekday = WEEKDAY_CN[tomorrow.weekday()]

    # 判断训练类型
    # 注意: 中文"速度训练"也视为ST类
    is_st = any(kw in sport for kw in ["st", "冲刺", "加速", "速度", "speed", "200m", "400m"])
    is_lt = any(kw in sport for kw in ["lt", "threshold", "阈值", "t区", "t跑"]) or \
            (hr_zone == "T区" and dist_km >= 8)
    is_long = dist_km > 16
    is_m_pace = pace_sec and pace_sec < 260  # 快于4'20"/km

    # 连续跑步天数检查
    dates = sorted(set(a.get("raw_date", "") for a in all_activities if a.get("raw_date", "")))
    from datetime import datetime as dt2, timedelta as td2
    streak = 0
    for i in range(len(dates)):
        d = dt2.strptime(dates[-(i+1)], "%Y%m%d")
        expected = dt2.now() - td2(days=i)
        if d.date() == expected.date():
            streak += 1
        else:
            break

    # 连续跑步>=4天，强制建议休息
    if streak >= 4 and not is_st and not is_lt and not is_long:
        return tomorrow_weekday, "休息", f"已连续跑步{streak}天，建议休息一天让身体恢复。"

    if is_st:
        return tomorrow_weekday, "休息或极轻E跑", "ST后必须休息48h，明日建议休息或30分钟极轻松E区跑"
    if is_lt:
        return tomorrow_weekday, "休息或极轻E跑", "阈值训练后需要48h恢复，明日建议休息或30分钟极轻松E区跑"
    if is_long:
        return tomorrow_weekday, "休息", f"{dist_km:.0f}km长跑后必须休息48h，明日建议完全休息"
    if is_m_pace and dist_km > 10:
        return tomorrow_weekday, "休息或极轻E跑", "马拉松配速跑后建议休息或极轻松E区跑"

    # 默认建议
    return tomorrow_weekday, "E区轻松跑", f"明日{tomorrow_weekday}建议8-10km E区轻松跑，心率控制在Z2有氧耐力区(137-154bpm)"


def generate_daily_report(activities: list) -> str:
    """生成每日训练日报"""
    if not activities:
        return "今日暂无训练数据。"

    today_activity = activities[0]  # 已按日期降序，第一条是最新
    raw_date = today_activity.get("raw_date", "")
    milestone = get_milestone_info(raw_date)

    # 计算距离截止天数
    deadline_days = "N/A"
    if "还剩" not in milestone.get("status", ""):
        deadline_days = "已截止或已完成"

    stats = weekly_stats(activities)
    compare = compare_with_last_week(today_activity, activities)

    # 周级别分析
    weekly_analysis_parts = []
    e_check = weekly_80_20_check(activities)
    if e_check:
        weekly_analysis_parts.append(e_check)
    consec_check = consecutive_run_days_check(activities)
    if consec_check:
        weekly_analysis_parts.append(consec_check)

    # 里程碑倒计时
    milestone_countdown = ""
    try:
        if raw_date and len(raw_date) == 8:
            y, m, d = int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:8])
            today_dt = datetime(y, m, d)
            deadline_str = milestone["deadline"]
            import re
            dm = re.search(r"(\d+)月(\d+)日", deadline_str)
            if dm:
                deadline_dt = datetime(y, int(dm.group(1)), int(dm.group(2)))
                days_left = (deadline_dt - today_dt).days
                if days_left > 0 and days_left <= 14:
                    milestone_countdown = f"   ⏰ 距离截止还剩{days_left}天，建议本周内安排测试/训练。"
                elif days_left > 0:
                    milestone_countdown = f"   ⏰ 还剩{days_left}天"
                elif days_left == 0:
                    milestone_countdown = "   ⏰ 今天截止！"
                else:
                    milestone_countdown = "   （已过期）"
    except Exception:
        pass

    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today_weekday = weekday_cn[datetime.now().weekday()]

    tomorrow_weekday, training_type, training_desc = next_day_suggestion(today_activity, activities)

    # 配速对比
    pace_compare_str = ""
    if compare.get("pace_diff_sec") is not None:
        diff = compare["pace_diff_sec"]
        sign = "+" if diff > 0 else ""
        pace_compare_str = f"，配速{sign}{diff}秒/km"

    # 跑量对比
    dist_compare_str = ""
    if compare:
        dist_diff = compare.get("dist_diff_km", 0)
        sign = "+" if dist_diff > 0 else ""
        dist_compare_str = f"，跑量{sign}{dist_diff}km"

    # 里程碑行（含倒计时）
    deadline_line = f"   截止：{milestone['deadline']}{milestone_countdown}" if milestone_countdown else f"   截止：{milestone['deadline']}"

    # 周分析区块
    weekly_analysis_block = ""
    if weekly_analysis_parts:
        weekly_analysis_block = "\n📊 关键指标\n"
        for part in weekly_analysis_parts:
            weekly_analysis_block += f"- {part}\n"

    report = f"""🏃 教练日报 | {today_activity.get('date', '今天')} {today_weekday}

━━━━━━━━━━━━━━━━━━━━━━
🎯 当前里程碑：{milestone['name']}
   目标：{milestone['target']}
{deadline_line}
   状态：{milestone['status']}
━━━━━━━━━━━━━━━━━━━━━━

【今日训练】
- 运动：{today_activity.get('sport', '跑步')}
- 距离：{today_activity.get('dist', '-')} | 配速：{today_activity.get('pace', '-')} | 心率：{today_activity.get('hr', '-')} bpm
- 训练负荷（TL）：{today_activity.get('tl', '-')}

📊 数据分析
- 心率区：{today_activity.get('hr_zone', '-')} {get_hr_analysis(today_activity)}
- 较上周同期：跑量{dist_compare_str or '（无上周同期数据）'}{pace_compare_str or ''}
- 本周累计（{stats.get('week_start', '')}至今）：{stats.get('dist_km', 0)}km / 负荷 {stats.get('total_tl', 0)}{weekly_analysis_block}

💬 训练点评
{get_training_comment(today_activity)}

📅 明日建议（{tomorrow_weekday}·{training_type}）
{training_desc}
"""
    return report


def get_hr_analysis(activity: dict) -> str:
    """根据心率区给出分析"""
    zone = activity.get("hr_zone", "")
    pace_sec = activity.get("pace_sec")
    dist_km = activity.get("dist_km", 0)

    if zone in ["E区", "Z2有氧耐力"]:
        if pace_sec and pace_sec > 390:  # 慢于6'30"
            return "→ 偏慢，Z2有氧耐力区OK，维持心率即可"
        return "→ 良好，Z2有氧基础训练到位"
    elif zone in ["灰色区", "Z3灰色"]:
        return "→ ⚠️ 灰色区！既没练有氧又没刺激阈值，建议降速进Z2"
    elif zone in ["T区", "Z4乳酸阈"]:
        return "→ 阈值区，强度适中，注意休息"
    elif zone == "A区" or zone == "I区":
        return "→ 高强度区，神经肌肉刺激，注意48h恢复"
    return ""


    # ─── 新增：周级别分析 ───

def weekly_80_20_check(activities: list) -> str:
    """检查本周E区占比是否满足80/20原则"""
    if len(activities) < 2:
        return ""
    e_tl = sum(a.get("tl", 0) or 0 for a in activities if a.get("hr_zone") == "E区")
    total_tl = sum(a.get("tl", 0) or 0 for a in activities)
    if total_tl == 0:
        return ""
    e_pct = e_tl / total_tl * 100
    if e_pct < 50:
        return f"⚠️ 本周E区占比仅{e_pct:.0f}%，远低于80/20原则要求的80%。大部分训练强度偏高（灰色区/Z3或更高），这会削弱有氧基础。"
    elif e_pct < 70:
        return f"⚠️ 本周E区占比{e_pct:.0f}%，未达到80/20原则的80%目标。注意控制轻松跑心率在Z2有氧耐力区(137-154bpm)。"
    return ""


def consecutive_run_days_check(activities: list) -> str:
    """检查连续跑步天数"""
    dates = sorted(set(a.get("raw_date", "") for a in activities if a.get("raw_date", "")))
    if not dates:
        return ""
    from datetime import datetime, timedelta
    today = datetime.now()
    streak = 0
    for i in range(len(dates)):
        d = datetime.strptime(dates[-(i+1)], "%Y%m%d")
        expected = today - timedelta(days=i)
        if d.date() == expected.date():
            streak += 1
        else:
            break
    if streak >= 4:
        return f"⚠️ 已连续跑步{streak}天，身体需要完全休息日。建议明日休息。"
    elif streak >= 3:
        return f"连续跑步{streak}天，明日可安排E跑或休息。"
    return ""


def get_training_comment(activity: dict) -> str:
    """根据训练内容给出点评"""
    sport = activity.get("sport", "").lower()
    dist_km = activity.get("dist_km", 0)
    zone = activity.get("hr_zone", "")
    pace_sec = activity.get("pace_sec")
    hr = activity.get("hr", 0)

    comments = []

    is_recovery = any(kw in sport for kw in ["恢复跑", "恢复", "recovery"])
    is_easy = any(kw in sport for kw in ["轻松跑", "easy"])

    # 灰色区漂移检测：标注"轻松跑"或"恢复跑"但心率在灰色区(Z3)
    if is_easy and zone in ["灰色区", "Z3灰色"]:
        comments.append(f"⚠️ 轻松跑心率{hr}bpm在灰色区Z3(155-162bpm)，偏快！Z2有氧耐力区上限154bpm，建议放慢节奏。")
    elif is_easy and zone == "E区":
        comments.append(f"✅ 轻松跑心率{hr}bpm在Z2有氧耐力区，符合有氧基础训练目标。")
    if is_recovery and zone in ["灰色区", "Z3灰色"]:
        comments.append(f"⚠️ 恢复跑心率{hr}bpm偏高（灰色区）！恢复跑应保持在Z2(<155bpm)，否则失去恢复效果。")
    elif is_recovery and zone == "E区":
        comments.append(f"✅ 恢复跑执行正确，心率{hr}bpm在Z2有氧耐力区，有效促进身体恢复。")

    if dist_km > 24:
        comments.append(f"超长跑 {dist_km:.0f}km，肌肉耐力训练到位，注意营养和睡眠补充。")
    elif dist_km > 16:
        comments.append(f"长距离跑 {dist_km:.0f}km，有氧耐力有效积累。")
    elif dist_km > 10:
        comments.append(f"{dist_km:.0f}km 中距离跑，训练量适中。")

    if "st" in sport or "冲刺" in sport or "加速" in sport or "速度" in sport:
        comments.append("冲刺训练，神经肌肉速度能力得到刺激。")
    if "lt" in sport or "阈值" in sport:
        comments.append("阈值训练，乳酸清除能力得到提升。")

    if zone == "E区" and pace_sec and pace_sec < 360:
        comments.append("E区跑配速偏快（<6'00\"），建议放松心态，以心率为准不要追配速。")
    elif zone == "I区" or zone == "A区":
        comments.append("高强度训练，注意观察身体状态，确保充分恢复。")

    if not comments:
        comments.append("训练完成，保持节奏。")

    return " ".join(comments)


# ─── 主入口 ───

def main():
    parser = argparse.ArgumentParser(description="Running Coach — 跑步教练数据获取")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--from-date", type=str, default=None)
    parser.add_argument("--to-date", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--daily-report", action="store_true")
    args = parser.parse_args()

    if args.from_date and args.to_date:
        date_from, date_to = args.from_date, args.to_date
    else:
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=args.days - 1)).strftime("%Y-%m-%d")

    print(f"[INFO] 抓取 {date_from} ~ {date_to}", file=sys.stderr)

    # 尝试从缓存加载
    cached = load_cache(date_from, date_to)
    if cached:
        activities = cached
        print(f"[CACHE] 从缓存加载 {len(activities)} 条活动", file=sys.stderr)
    else:
        activities = fetch_activities(date_from, date_to, headless=not args.visible)

    result = {
        "fetched_at": datetime.now().isoformat(),
        "date_from": date_from,
        "date_to": date_to,
        "count": len(activities),
        "activities": activities,
    }

    # 保存缓存
    save_cache(result)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[OK] 已保存到 {args.output}", file=sys.stderr)

    if args.daily_report:
        report = generate_daily_report(activities)
        print(report)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    main()
