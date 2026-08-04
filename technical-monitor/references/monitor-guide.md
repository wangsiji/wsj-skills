# 技术指标监控 · 参考指南

本文件是 `technical-monitor` 技能的详细说明，供执行时按需读取。SKILL.md 只保留核心流程。

## 一、数据源与依赖

- 行情接口：`westock-data` 技能自带的 Node 脚本 `scripts/index.js`。
- 通过 `subprocess` 调用，需本机 Node 与 westock-data 脚本路径正确。
- 默认路径（已写入脚本，可用环境变量覆盖）：
  - `NODE_BIN`：Node 可执行文件
  - `WESTOCK_INDEX`：westock-data 的 `index.js` 路径
  - `MONITOR_OUT_DIR`：信号/状态文件输出目录（默认 Obsidian 的 `03-Resources/Notes`）
- 拉取命令（脚本内部已处理）：
  - 日K：`kline <code> --period day --start <130天前> --end <今天>`
  - 周K：`kline <code> --period week --start 2024-01-01 --end <今天>`
  - 一律加 `--raw` 取原始 JSON。
- **限流处理**：`fetch_json` 带 5 次重试、间隔 2 秒，规避接口偶发空返回/限流。
- **不要用** `technical` 命令取 CCI —— 该接口不含 CCI，且范围过大易失败。CCI/KDJ/MACD 一律用 K线 OHLC 自算（算法见下），更稳定。

## 二、指标算法（纯标准库，与主流软件一致）

- **EMA**：`E = price*k + E_prev*(1-k)`, `k = 2/(n+1)`，初值取首价。
- **MACD(12,26,9)**：DIF = EMA12 − EMA26；DEA = EMA(DIF, 9)；柱 = 2*(DEA − DIF)。
- **CCI(14)**：TP = (H+L+C)/3；MA = 窗口均值；MD = 窗口 |TP−MA| 均值；CCI = (TP−MA)/(0.015*MD)。
- **KDJ(9,3,3)**：每根 K 线取近 9 根 RSV；K = 2/3·K_prev + 1/3·RSV；D = 2/3·D_prev + 1/3·K；J = 3K − 2D；初始 K=D=50。

## 三、6 类触发条件（默认阈值 = 159659 原规则）

| # | 条件 | 默认阈值 | 方向 |
|---|------|---------|------|
| 1 | 日线 MACD 柱由正转负 / 由负转正（零轴穿越） | — | 提醒（动能切换） |
| 2 | 日线 J < J_BUY 且 CCI > CCI_BUY | J_BUY=10, CCI_BUY=−100 | 买入 |
| 3 | 日线 J > J_SELL 且 \|CCI−100\| ≤ CCI_SELL_TOL | J_SELL=100, CCI_SELL_TOL=10 | 卖出 |
| 4 | 周线 CCI < WCCI_BUY 且 J < J_BUY | WCCI_BUY=−50 | 买入 |
| 5 | 周线 J > J_SELL 且 CCI > WCCI_SELL | WCCI_SELL=100 | 卖出 |
| 6 | 成交量共振：买卖触发时量比≥VOL_HIGH 为放量确认，≤VOL_LOW 为缩量企稳 | VOL_HIGH=1.5, VOL_LOW=0.7 | 辅助确认 |

- 所有阈值均可经命令行覆盖（见 SKILL.md 用法）。
- **去重**：状态文件记录上一跑的 `macd_sign` / `buy` / `sell`；仅在「非触发→触发」的**状态切换**时输出新触发，避免每天重复提醒。历史保留最近 50 条。

## 四、输出文件

- `<NAME>-监控信号.md`：人类可读信号卡（指标快照 / 本次触发 / 持续状态 / 历史 / 规则速查）。
- `<NAME>-监控状态.json`：机器状态（去重用），文件名由 `--name` 决定。

## 五、自动化（Automation）配置示例

用 `automation_update` 建两个定时任务，分别驱动日/周监控：

1. **日线监控**（交易日 16:05）：
   - `rrule`: `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=16;BYMINUTE=5`
   - `prompt`: 运行 `python3 <skill>/scripts/monitor.py --code sz159659 --mode daily --name 159659 --premium 8.62`
2. **周线监控**（周五 16:10）：
   - `rrule`: `FREQ=WEEKLY;BYDAY=FR;BYHOUR=16;BYMINUTE=10`
   - `prompt`: 运行 `python3 <skill>/scripts/monitor.py --code sz159659 --mode weekly --name 159659 --premium 8.62`

> 注：日/周两种模式都会评估全部 6 条件（仅 stdout/标题不同），因此无论哪个定时先跑都不会漏信号。

## 六、常见坑

- `kline --period day` 必须用 `--start/--end`，不能用 `--limit`（会返回空）。
- `technical` 命令只支持 ma/macd/kdj/rsi/boll/bias/wr/dmi/all，**无 CCI**，且易因范围过大失败 —— 故自算。
- 接口偶发限流/空返回 —— 依赖 `fetch_json` 重试，勿去掉重试。
- 溢价（QDII ETF 常见）意味着任何「买入」信号先承担溢价成本，务必在信号文件提示（用 `--premium`）。
