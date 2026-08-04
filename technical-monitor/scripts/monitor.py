#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标条件监控 (通用版)
========================
对任意 A股/港股/美股 ETF 或个股做 KDJ / CCI / MACD 技术信号监控。
数据源: westock-data (腾讯自选股行情接口)
指标: 日/周线 KDJ(9,3,3)、CCI(14)、MACD(12,26,9)柱、成交量比

触发条件 (共6类, 阈值均可命令行覆盖):
  监控1 (日MACD柱零轴切换): 日线 MACD 柱 由正转负 / 由负转正 -> 提醒
  日买入: 日线 KDJ.J < J_BUY(默认10)  且  日线 CCI > CCI_BUY(默认-100)
  日卖出: 日线 KDJ.J > J_SELL(默认100) 且  |日线 CCI - 100| <= CCI_SELL_TOL(默认10)
  周买入: 周线 CCI < WCCI_BUY(默认-50) 且  周线 KDJ.J < J_BUY(默认10)
  周卖出: 周线 KDJ.J > J_SELL(默认100) 且  周线 CCI > WCCI_SELL(默认100)
  成交量共振: 买卖信号触发时, 量比(近20日均量) >= VOL_HIGH(默认1.5x)为放量确认, <= VOL_LOW(默认0.7x)为缩量企稳

用法:
  python3 monitor.py --code sz159659 --mode daily
  python3 monitor.py --code sz159659 --mode weekly --name 159659
  python3 monitor.py --code usAAPL   --mode daily --out-dir /path/to/notes --premium 0

说明:
  --code   标的代码 (westock-data 格式, 如 sz159659 / sh510300 / usAAPL / hk00700)
  --name   信号/状态文件基名 (默认=code; 159659 场景传 159659 以沿用旧文件名)
  --mode   daily / weekly (两种模式均会评估全部6条件, 仅 stdout/标题标签不同)
  --out-dir 信号与状态文件输出目录 (默认见下方 NOTES 路径)
  --premium 场内溢价百分比, >0 时在信号文件顶部加溢价风险提示

依赖: westock-data 技能脚本 (见下方 WESTOCK 默认路径, 可用环境变量 WESTOCK_INDEX / NODE_BIN 覆盖)
免责: 技术指标仅为量化参考, 不构成投资建议, 不承诺收益。
"""
import argparse
import json
import os
import subprocess
import sys
import time
import datetime
from pathlib import Path


def os_env(key, default):
    return os.environ.get(key, default)


# ---- 环境与路径 (可用环境变量覆盖, 便于迁移到其他机器) ----
NODE = os_env("NODE_BIN", "/usr/bin/node")
WESTOCK = os_env(
    "WESTOCK_INDEX",
    "/home/wangsiji/.local/westock/scripts/index.js",
)
NOTES = Path(
    os_env(
        "MONITOR_OUT_DIR",
        "/home/wangsiji/projects/wsj-second-brain/03-Resources/Notes",
    )
)


# ---------- 数据拉取 ----------
def run_westock(args):
    cmd = [NODE, WESTOCK] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError("westock error: " + r.stderr[:500])
    return r.stdout


def get_json(args):
    out = run_westock(args + ["--raw"])
    data = json.loads(out)
    if isinstance(data, dict) and data.get("success") is False:
        raise RuntimeError("API fail: " + str(data.get("error", {}).get("message")))
    # technical 命令返回 {"success":true,"data":[...]}; kline 直接返回列表 -> 统一取 data
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"]
    return data


def fetch_json(args, retries=5, delay=2.0):
    """带重试的拉取, 规避接口限流/偶发空返回"""
    last = None
    for i in range(retries):
        try:
            data = get_json(args)
        except RuntimeError as e:
            last = e
            if i < retries - 1:
                time.sleep(delay)
                continue
            raise
        if isinstance(data, list) and len(data) == 0:
            last = RuntimeError("empty result for " + " ".join(args))
            if i < retries - 1:
                time.sleep(delay)
                continue
            return data
        return data
    if last:
        raise last
    return data


# ---------- 指标计算 (纯标准库) ----------
def ema(vals, n):
    if not vals:
        return []
    k = 2.0 / (n + 1)
    res = [vals[0]]
    for i in range(1, len(vals)):
        res.append(vals[i] * k + res[-1] * (1 - k))
    return res


def macd(closes):
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    dif = [a - b for a, b in zip(e12, e26)]
    dea = ema(dif, 9)
    bar = [2 * (d - x) for d, x in zip(dea, dif)]
    return dif, dea, bar


def cci(highs, lows, closes, n=14):
    tps = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    res = [None] * len(tps)
    for i in range(n - 1, len(tps)):
        window = tps[i - n + 1:i + 1]
        ma = sum(window) / n
        md = sum(abs(x - ma) for x in window) / n
        res[i] = 0.0 if md == 0 else (tps[i] - ma) / (0.015 * md)
    return res


def kdj(highs, lows, closes, n=9):
    size = len(closes)
    k = [None] * size
    d = [None] * size
    j = [None] * size
    kv = 50.0
    dv = 50.0
    for i in range(n - 1, size):
        hh = max(highs[i - n + 1:i + 1])
        ll = min(lows[i - n + 1:i + 1])
        rsv = 50.0 if hh == ll else (closes[i] - ll) / (hh - ll) * 100
        kv = 2.0 / 3 * kv + 1.0 / 3 * rsv
        dv = 2.0 / 3 * dv + 1.0 / 3 * kv
        k[i] = kv
        d[i] = dv
        j[i] = 3 * kv - 2 * dv
    return k, d, j


# ---------- 状态管理 (避免重复提醒) ----------
def load_state(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"daily": {}, "weekly": {}, "history": []}


def save_state(st, path):
    path.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def vol_note(ratio, vol_high, vol_low):
    if ratio >= vol_high:
        return f"放量确认({ratio:.2f}x)"
    if ratio <= vol_low:
        return f"缩量企稳({ratio:.2f}x)"
    return f"量能中性({ratio:.2f}x)"


# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser(description="技术指标条件监控 (通用版)")
    ap.add_argument("--code", required=True, help="标的代码, 如 sz159659 / sh510300 / usAAPL / hk00700")
    ap.add_argument("--name", default=None, help="信号/状态文件基名 (默认=code)")
    ap.add_argument("--mode", choices=("daily", "weekly"), default="daily")
    ap.add_argument("--out-dir", default=str(NOTES), help="信号与状态文件输出目录")
    ap.add_argument("--premium", type=float, default=0.0, help="场内溢价百分比, >0 时加风险提示")
    # 阈值可覆盖
    ap.add_argument("--j-buy", type=float, default=10.0)
    ap.add_argument("--j-sell", type=float, default=100.0)
    ap.add_argument("--cci-buy", type=float, default=-100.0)
    ap.add_argument("--cci-sell-tol", type=float, default=10.0)
    ap.add_argument("--wcci-buy", type=float, default=-50.0)
    ap.add_argument("--wcci-sell", type=float, default=100.0)
    ap.add_argument("--vol-high", type=float, default=1.5)
    ap.add_argument("--vol-low", type=float, default=0.7)
    args = ap.parse_args()

    name = args.name or args.code
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    signal_file = out_dir / f"{name}-监控信号.md"
    state_file = out_dir / f"{name}-监控状态.json"
    code = args.code

    today = datetime.date.today()
    start = (today - datetime.timedelta(days=130)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    day_k = fetch_json(["kline", code, "--period", "day", "--start", start, "--end", end])
    week_k = fetch_json(["kline", code, "--period", "week", "--start", "2024-01-01", "--end", end])

    # 日K
    day_k.sort(key=lambda x: x["date"])
    dh = [b["high"] for b in day_k]
    dl = [b["low"] for b in day_k]
    dc = [b["last"] for b in day_k]
    day_vol = [b["volume"] for b in day_k]
    dcci = cci(dh, dl, dc, 14)
    _, _, dbar = macd(dc)
    _, _, dj = kdj(dh, dl, dc)

    dj_last = dj[-1]
    dj_prev = dj[-2] if len(dj) > 1 else dj[-1]
    dcci_last = dcci[-1]
    dcci_prev = dcci[-2] if len(dcci) > 1 else dcci[-1]
    dbar_last = dbar[-1]
    dbar_prev = dbar[-2] if len(dbar) > 1 else dbar[-1]
    dv_last = day_vol[-1]
    dv_avg = sum(day_vol[-21:-1]) / 20 if len(day_vol) > 20 else (sum(day_vol[:-1]) / max(1, len(day_vol) - 1))
    vol_ratio = dv_last / dv_avg if dv_avg else 1.0

    # 周K
    if not week_k:
        wj_last = None
        wcci_last = None
    else:
        week_k.sort(key=lambda x: x["date"])
        wh = [b["high"] for b in week_k]
        wl = [b["low"] for b in week_k]
        wc = [b["last"] for b in week_k]
        wk, wkd, wj = kdj(wh, wl, wc)
        wcci = cci(wh, wl, wc, 14)
        wj_last = wj[-1]
        wcci_last = wcci[-1]

    # 判断 (阈值来自 args, 默认即 159659 原规则)
    macd_cross = None
    if dbar_prev is not None and dbar_last is not None:
        if dbar_prev <= 0 < dbar_last:
            macd_cross = "上穿零轴(动能转多/金叉区)"
        elif dbar_prev >= 0 > dbar_last:
            macd_cross = "下穿零轴(动能转空/死叉区)"

    day_buy = (dj_last < args.j_buy) and (dcci_last is not None and dcci_last > args.cci_buy)
    day_sell = (dj_last > args.j_sell) and (dcci_last is not None and abs(dcci_last - 100) <= args.cci_sell_tol)
    week_buy = (wj_last is not None and wj_last < args.j_buy) and (wcci_last is not None and wcci_last < args.wcci_buy)
    week_sell = (wj_last is not None and wj_last > args.j_sell) and (wcci_last is not None and wcci_last > args.wcci_sell)

    # 状态 & 新触发 (daily/weekly 模式均判断全部条件, 仅 stdout/标题标签不同)
    st = load_state(state_file)
    history = st.get("history", [])
    new_triggers = []
    last_d = st.get("daily", {})
    last_w = st.get("weekly", {})
    cur_macd_sign = "pos" if dbar_last > 0 else ("neg" if dbar_last < 0 else "zero")
    if macd_cross and last_d.get("macd_sign") != cur_macd_sign:
        new_triggers.append(("日MACD柱" + macd_cross, f"柱值{dbar_last:.4f}"))
    if day_buy and not last_d.get("buy"):
        new_triggers.append(("日线买入信号", f"J={dj_last:.1f}, CCI={dcci_last:.1f}, {vol_note(vol_ratio, args.vol_high, args.vol_low)}"))
    if day_sell and not last_d.get("sell"):
        new_triggers.append(("日线卖出信号", f"J={dj_last:.1f}, CCI={dcci_last:.1f}, {vol_note(vol_ratio, args.vol_high, args.vol_low)}"))
    if week_buy and not last_w.get("buy"):
        new_triggers.append(("周线买入信号", f"J={wj_last:.1f}, CCI={wcci_last:.1f}"))
    if week_sell and not last_w.get("sell"):
        new_triggers.append(("周线卖出信号", f"J={wj_last:.1f}, CCI={wcci_last:.1f}"))
    st["daily"] = {"macd_sign": cur_macd_sign, "buy": day_buy, "sell": day_sell, "updated": end}
    st["weekly"] = {"buy": week_buy, "sell": week_sell, "updated": end}

    for nm, detail in new_triggers:
        history.append({"date": end, "type": nm, "detail": detail})
    st["history"] = history[-50:]
    save_state(st, state_file)

    # 写信号文件
    wj_s = wj_last if wj_last is not None else 0.0
    wcci_s = wcci_last if wcci_last is not None else 0.0
    cur_macd_sign = "pos" if dbar_last > 0 else ("neg" if dbar_last < 0 else "zero")
    lines = []
    lines.append(f"# {name} 技术指标监控信号")
    lines.append("")
    lines.append(f"> 扫描时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 数据截至: {end} ｜ 标的: {code}")
    lines.append(">")
    if args.premium > 0:
        lines.append(f"> ⚠️ 当前场内溢价约 {args.premium:.2f}%，任何『买入』信号都先承担溢价成本。技术指标仅为量化参考，不构成投资建议，不承诺收益。")
    else:
        lines.append("> ⚠️ 技术指标仅为量化参考，不构成投资建议，不承诺收益。")
    lines.append("")
    lines.append("## 一、当前指标快照")
    lines.append("")
    lines.append("| 周期 | 指标 | 最新值 | 状态 |")
    lines.append("|---|---|---|---|")
    lines.append(f"| 日线 | KDJ.J | {dj_last:.2f} | {'<'+str(args.j_buy)+' 买入区' if dj_last < args.j_buy else ('>'+str(args.j_sell)+' 卖出区' if dj_last > args.j_sell else '中性')} |")
    lines.append(f"| 日线 | CCI(14) | {dcci_last:.2f} | {'>'+str(args.cci_buy) if dcci_last > args.cci_buy else '<='+str(args.cci_buy)} |")
    lines.append(f"| 日线 | MACD柱 | {dbar_last:.4f} | {'零轴上(多)' if dbar_last > 0 else '零轴下(空)'} |")
    lines.append(f"| 日线 | 量比 | {vol_ratio:.2f}x | {vol_note(vol_ratio, args.vol_high, args.vol_low)} |")
    lines.append(f"| 周线 | KDJ.J | {wj_s:.2f} | {'<'+str(args.j_buy)+' 买入区' if wj_s < args.j_buy else ('>'+str(args.j_sell)+' 卖出区' if wj_s > args.j_sell else '中性')} |")
    lines.append(f"| 周线 | CCI(14) | {wcci_s:.2f} | {'<'+str(args.wcci_buy) if wcci_s < args.wcci_buy else ('>'+str(args.wcci_sell) if wcci_s > args.wcci_sell else '中性')} |")
    lines.append("")
    lines.append("## 二、本次触发（" + args.mode + " 模式）")
    lines.append("")
    if new_triggers:
        for nm, detail in new_triggers:
            lines.append(f"- 🔔 **{nm}** — {detail}")
    else:
        lines.append("- 无新触发（持续状态见下方）")
    lines.append("")
    lines.append("## 三、持续状态（满足条件但未新触发）")
    lines.append("")
    cont = []
    if day_buy:
        cont.append(f"日线买入条件持续满足 (J={dj_last:.1f}, CCI={dcci_last:.1f}, {vol_note(vol_ratio, args.vol_high, args.vol_low)})")
    if day_sell:
        cont.append(f"日线卖出条件持续满足 (J={dj_last:.1f}, CCI={dcci_last:.1f}, {vol_note(vol_ratio, args.vol_high, args.vol_low)})")
    if week_buy:
        cont.append(f"周线买入条件持续满足 (J={wj_s:.1f}, CCI={wcci_s:.1f})")
    if week_sell:
        cont.append(f"周线卖出条件持续满足 (J={wj_s:.1f}, CCI={wcci_s:.1f})")
    if macd_cross is None:
        cont.append(f"日MACD柱位于{cur_macd_sign}方(无零轴切换)")
    if not cont:
        cont.append("无")
    for c in cont:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## 四、触发历史（最近）")
    lines.append("")
    if history:
        for h in reversed(history[-15:]):
            lines.append(f"- {h['date']} · {h['type']} · {h['detail']}")
    else:
        lines.append("- 暂无")
    lines.append("")
    lines.append("## 五、触发规则速查")
    lines.append("")
    lines.append("- 监控1: 日线MACD柱 由正转负 / 由负转正（零轴穿越）")
    lines.append(f"- 日买入: 日线 J<{args.j_buy} 且 CCI>{args.cci_buy}")
    lines.append(f"- 日卖出: 日线 J>{args.j_sell} 且 |CCI-100|<={args.cci_sell_tol}")
    lines.append(f"- 周买入: 周线 CCI<{args.wcci_buy} 且 J<{args.j_buy}")
    lines.append(f"- 周卖出: 周线 J>{args.j_sell} 且 CCI>{args.wcci_sell}")
    lines.append(f"- 成交量: 买卖信号触发时量比>={args.vol_high}x为放量确认, <={args.vol_low}x为缩量企稳")
    signal_file.write_text("\n".join(lines), encoding="utf-8")

    # stdout 摘要 (供 automation 捕获)
    print(f"[{name} 监控/{args.mode}] 数据截至 {end}")
    print(f"  日线 J={dj_last:.1f} CCI={dcci_last:.1f} MACD柱={dbar_last:.4f}({cur_macd_sign}) 量比={vol_ratio:.2f}x")
    print(f"  周线 J={wj_s:.1f} CCI={wcci_s:.1f}")
    if new_triggers:
        print("  🔔 新触发:")
        for n, d in new_triggers:
            print(f"    - {n}: {d}")
    else:
        print("  本次无新触发")


if __name__ == "__main__":
    main()
