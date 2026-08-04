---
name: technical-monitor
description: "股票技术指标(KDJ/CCI/MACD)条件监控与去重提醒,数据源 westock-data。"
version: 1.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [股票, 技术分析, 监控, 量化, westock-data]
    category: custom
---

# Technical Monitor · 技术指标条件监控

## Overview

对任意标的（A股/港股/美股 ETF 或个股）拉取日/周 K 线，自算 KDJ(9,3,3)、CCI(14)、MACD(12,26,9) 柱与量比，按 6 类条件评估买卖/动能信号，写入人类可读的信号 Markdown 文件，并通过状态文件**去重**（仅在状态切换时提醒）。设计为可配置阈值的通用技能，默认参数即 159659 纳斯达克100ETF 的实战规则。

## When to Use

- 用户要"监控某只股票/ETF 的几个技术指标并提醒"
- 出现"日K里 J<10 且 CCI>-100 提醒买入 / J>100 且 CCI≈100 提醒卖出"类条件单需求
- 周K 的 CCI/KDJ 组合买入/卖出提醒
- 把技术条件监控做成可定时运行的自动化任务
- 需对任意标的复用同一套 KDJ/CCI/MACD 监控逻辑

## Workflow

### 1. 确定标的与参数

解析用户需求中的：代码（如 `sz159659`/`sh510300`/`usAAPL`/`hk00700`）、监控周期（daily/weekly 或两者）、以及任何自定义阈值。默认阈值（J_BUY=10, CCI_BUY=−100, J_SELL=100, CCI_SELL_TOL=10, WCCI_BUY=−50, WCCI_SELL=100, VOL_HIGH=1.5, VOL_LOW=0.7）对应 159659 规则；其他标的用 `--j-buy` 等覆盖。

### 2. 运行监控脚本

执行 `scripts/monitor.py`（详见 `references/monitor-guide.md` 的算法与坑位说明）：

```bash
# 159659 日线 (沿用旧文件名 159659-监控信号.md, 带溢价提示)
python3 <skill>/scripts/monitor.py --code sz159659 --mode daily --name 159659 --premium 8.62

# 159659 周线
python3 <skill>/scripts/monitor.py --code sz159659 --mode weekly --name 159659 --premium 8.62

# 任意标的, 自定义阈值与输出目录
python3 <skill>/scripts/monitor.py --code usAAPL --mode daily --out-dir /path/to/notes
```

脚本内部：调用 westock-data 取日/周 K 线 → 自算 KDJ/CCI/MACD/量比 → 评估 6 条件 → 比对状态文件去重 → 写 `<NAME>-监控信号.md` 与 `<NAME>-监控状态.json` → stdout 输出摘要。

### 3. 读取与解读结果

- 信号文件含：当前指标快照表、本次触发（状态切换才记）、持续状态、触发历史、规则速查。
- stdout 摘要供 Automation 捕获；`🔔` 行为新触发。
- **关键判读**：动能切换（MACD 柱零轴穿越）≠ 买卖信号；买入信号须叠加溢价提示（QDII ETF 常见），任何买入先承担溢价成本。

### 4. 建立定时自动化（可选）

用 `automation_update` 建日线（交易日 16:05）与周线（周五 16:10）两个定时任务，prompt 分别运行上面的 daily / weekly 命令。两种模式均评估全部 6 条件，不会漏信号。配置示例见 `references/monitor-guide.md` 第五节。

### 5. 复用与迁移

- 换标的：改 `--code`；换文件名基名：改 `--name`；换输出目录：改 `--out-dir` 或环境变量 `MONITOR_OUT_DIR`。
- 迁移机器：用环境变量 `NODE_BIN` / `WESTOCK_INDEX` 指向新环境的 Node 与 westock-data 脚本。

## Resources

- **scripts/monitor.py** — 核心监控脚本（纯标准库，参数化，去重，写信号/状态文件）。
- **references/monitor-guide.md** — 数据源、指标算法、6 条件表、自动化示例、常见坑。

## 免责

技术指标仅为量化参考，不构成投资建议，不承诺收益。溢价 ETF 的买入信号须先计溢价成本。
