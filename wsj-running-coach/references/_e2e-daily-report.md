---
name: e2e-daily-report
description: 端到端教练日报命令序列——running_coach.py 取运动 + coros-mcp 取睡眠/HRV，手动调试或合成日报时用。2026-07-19 实测可用。
---

# 端到端日报命令序列（手动 / 调试用）

> 2026-07-19 实测可用。cron 自动跑时由 skill 的「自动化」段 prompt 驱动，本文件供手动验证/排错。

## 步骤

### 1. 运动数据（Playwright，~55–180s）
```bash
timeout 180 python3 ~/.hermes/skills/custom/running-coach/scripts/running_coach.py --days 7 --daily-report
```
- 输出最新一天训练报告（**不含睡眠**，需步骤 2 补）
- 登录 40–50s + 拉 340 条记录，前台 60s 会超时 → 必须 `timeout 180`

### 2. 睡眠分期（coros-mcp，已认证 region=asia，走 Mobile API 真实数据）
```bash
cd ~/projects/coros-mcp && .venv/bin/python -c "import asyncio,json; from server import get_sleep_data; print(json.dumps(asyncio.run(get_sleep_data(weeks=1)),ensure_ascii=False))"
```
- 返回：`records[].phases.{deep,light,rem,awake}_minutes` + `avg_hr`/`min_hr`
- 失败 → 退回用户口述（不卡流程）

### 3. HRV / RHR / 训练负荷（可选，偶发超时）
```bash
cd ~/projects/coros-mcp && .venv/bin/python -c "import asyncio,json; from server import get_daily_metrics; print(json.dumps(asyncio.run(get_daily_metrics(weeks=1)),ensure_ascii=False))"
```
- 返回：`avg_sleep_hrv` / `rhr` / `training_load` / `ati` / `cti` / `tired_rate`
- 偶发超时返回空，重试一次；睡眠已覆盖恢复判断，HRV 缺失不影响日报

## 合成规则
- 睡眠自动填入日报「🌙 睡眠」行；失败则改口述
- **体重 / 肩带训练始终靠用户口述**（手表不测体重 + API 无字段；肩带为弹力带自练无数据）

## 认证前提
- `coros-mcp auth`（region=asia）已跑过，token 存 keyring
- 检查：`cd ~/projects/coros-mcp && .venv/bin/coros-mcp auth-status`
- 官方 `coroslab/COROS-MCP` 是浏览器 OAuth，无头 Telegram 环境跑不了（`OAuthNonInteractiveError`），故用社区版 `cygnusb/coros-mcp`
