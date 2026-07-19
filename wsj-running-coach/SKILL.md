---
name: wsj-running-coach
description: 跑步教练：当用户说"今天训练怎么样""教练日报""明天要跑测试/比赛"，或问配速/心率/间歇/乳酸阈/破三进度时，拉取 COROS 数据（运动+睡眠+HRV）生成训练反馈与阶段性计划，服务全马破三(<3:00)。
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [running, coros, marathon, training]
    category: health
---

# Running Coach（路由版 v2）

> 主文件只做路由 + 最高优先级规则。细分规则/数据/参考在 `references/`，按需读取。

## 黄金 5 条

1. 减重是破三最高杠杆（1kg≈3秒/km；当前真实体重 **138斤→目标125斤**，约 13斤 ≈ 39秒/km 可用，非 158→125 的 50秒）
2. 每次执行前拉最新 COROS 数据，不用缓存
3. vault 是真相源，skill 用户核心数据段为快照（过期不更新不代表目标变）
4. 睡眠/HRV 从 coros-mcp mobile API 自动获取，失败退口述
5. 体重：COROS **非官方 API 无体重接口**（已枚举确认 dayDetail/mobile statistic 均不含）；但**官方 MCP 的 `queryUserInfo` 已接入**——走 `coros-mcp/coros_weight.py`（OAuth Dynamic Client Registration + PKCE，token 存 `~/.hermes/coros_mcp_token.json`）。cron 每天 10:00 自动拉体重写 `体重数据.md`（见 `references/coros-official-mcp-weight.md`）。无每日历史序列 tool，返回的是 profile 最新值，cron 每日快照即可

## Rule Priority

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | 安全 | 周跑量增幅≤10%、高强度后48h恢复、连续高强度次日起休 |
| **P1** | 减重优先 | 体重每降1kg配速快~3s/km，减重与跑量并列优先级 |
| **P2** | 80/20 | 80% 跑量在 Z2(E区)，20% 在 Z4+(T/I)，灰色区 Z3 不是日常区 |
| **P3** | 耐力底盘 | 周跑量 > 连续天数 > 配速质量；先堆量再上强度 |
| **P4** | 三目标整合 | 破三 + 减重 + 肩带（每周≥2次弹力带/单杠，不抢跑步恢复） |

## Task Router

```
用户说"训练怎么样"/cron触发
  → 拉最近7天数据 → 生成日报 → references/daily-report-template.md
用户说"明天测试/比赛"
  → 检查里程碑 → 测试周计划 → references/vdot-prediction.md
用户说"膝盖疼/下雨/感冒"
  → 判断风险 → 调整方案 → references/heart-rate-zones.md
用户说「里程碑进度」
  → 查当前里程碑 → 进度报告 → 读 vault 马拉松比赛.md（倒推里程碑段）
用户说"睡眠/HRV/体重"
  → 睡眠/HRV → coros-mcp get_sleep_data/get_daily_metrics
  → 体重 → coros-mcp/coros_weight.py get_weight_kg()（官方 MCP queryUserInfo，cron 每日自动拉；手动记也行）
```

## 输入输出协议

**输入**：用户自然语言指令（训练反馈/测试/调整）
**输出**：日报模板 + 明日建议 + vault 运动周追踪表写入指引

## Pre-flight Check

- [ ] COROS 数据已拉最新（running_coach.py or coros-mcp）
- [ ] vault 健康主线已确认（10-健康.md + 马拉松比赛.md；⚠️ 2026-07-19 已删 `年底三目标训练总表.md`，破三规划已并入 `马拉松比赛.md`，勿再引用旧路径）
- [ ] 睡眠数据已取（coros-mcp get_sleep_data）
- [ ] 用户核心数据段标注过期风险

## Never Do

- ❌ 用缓存 COROS 数据（每次必须拉最新）
- ❌ 用 read_file() 读后直接写回 vault（行号污染）
- ❌ 内联密码（凭证从环境变量/keyring）
- ❌ 用 Web API dashboard/query 的 sleep 字段（缓存值，不可用）
- ❌ 在建设期（7-8月）安排全马测试（打乱巅峰期节奏）
- ❌ 为用户已在 COROS 安排/追踪的习惯（每日跑步、俯卧撑等）另建 vault 追踪文件 —— **一个项目一个文件**，数据从 COROS 拉，不重复建。用户原话：「尽量一个项目一个文件」
- ⚠️ `running_coach.py` 当前硬编码密码（违反上条「内联密码」）；cron 自动跑前先确认 playwright 可用。CLI 参数用 `--from-date`/`--to-date`（非 `--date-from`）

## 每日自动拉取（cron 模式）

- 命令：`python3 scripts/running_coach.py --from-date <昨天> --to-date <今天> --daily-report`
- 力量/俯卧撑活动按 `sportType` 一并拉取，无需单独处理（不要为此建 vault 文件）
- 用户说「每天拉训练」：设 cron 每天固定时间跑上述命令生成日报，发回对话
- 已验证可用命令：`timeout 150 python3 scripts/running_coach.py --from-date 2026-07-17 --to-date 2026-07-19 --daily-report` → 返回教练日报（playwright+chromium 链路通）

### cron 脚本落地规则（实测踩坑）

- **cron 的 `script` 字段必须放在 `~/.hermes/scripts/` 下**，只写文件名（如 `script: _cron_sync_coros.py`）。给绝对路径或 vault 内路径会被拒：`Script path must be relative to ~/.hermes/scripts/`。vault 里放的同名脚本需 `cp` 过去并删掉 vault 那份（避免重复）。
- **可用脚本**：`~/.hermes/scripts/_cron_sync_coros.py`（已建，job_id `818beb975a1f`，每天 **10:00**）。它走 **coros-mcp 程序化拉取**（非 Playwright），按 `sport_type`/`name` 区分跑步与俯卧撑，分别 `append_row` 进 `跑步数据.md` / `俯卧撑数据.md`；体重走 **官方 MCP**（`coros_weight.get_weight_kg()`，子进程调用，写 `体重数据.md`，同日去重）。无活动日输出「无 COROS 活动记录」不写库。详见 `references/coros-official-mcp-weight.md`。
- 复用 `running_coach.py` 内联密码重登（env 为空时）；子进程 `-c` 内嵌脚本务必 `import datetime`（否则空 stdout 时 `[-300]` 索引报错）。
- 区分跑步 vs 力量：`sport_type` 跑步≈1/6、力量≈2/3/4/5/7/8/9；或 `name` 含「跑/run」/「俯卧撑/push/力量」。

### ⚠️ 无头/cron 回退：实时同步失败 → 缓存聚合

高驰 SPA 在无头 chromium 下常不触发 `networkidle`，登录偶发超时，`--days 7` 还会因 `load_cache()` 只匹配单日精确窗而直接崩溃（拿不到数据也不回退）。**回退步骤：**

1. 先 `timeout 280 python3 scripts/running_coach.py --days 7 --daily-report` 重试一次（偶发超时可过）。
2. 仍失败 → 聚合 `~/.hermes/coros-cache/` 每日文件重建 7 天窗，做法见 `references/cron-cache-fallback.md`（按 `raw_date` 去重 + 过滤到目标窗，再 `generate_daily_report`）。
3. 「今日训练」若缓存里无当日记录，标「未记录（休息日/长还未同步）」，**绝不编造**。

⚠️ **cron 配置注意**：调度器里 skill 名若写 `running-coach` 会找不到（真实 skill 名 `wsj-running-coach`）；脚本真实路径是 `custom/wsj-running-coach/scripts/running_coach.py`（不是 `productivity/running-coach/`）。若 cron 报 skill not found，先核对这两项。

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/heart-rate-zones.md` | 心率分区 + 灰色区判断 |
| `references/running_general.md` | 80/20、配速、伤防理论底座 |
| `references/vdot-prediction.md` | VDOT 预测表 + 训练进步因子 |
| `references/screenshot-parsing.md` | COROS 截图 OCR 解析 |
| `references/coros-api.md` | COROS API 端点细节 |
| `references/coros-mcp.md` | coros-mcp 安装/cron限制 |
| `references/coros-data-pull.md` | **程序化拉取真实训练历史/计划的可用模板+踩坑**（async、distance_meters、token过期重登、env为空复用running_coach密码）|
| `references/tooling-details.md` | 程序化调用代码片段 |
| `references/body-composition.md` | 体重/体脂数据说明（官方 MCP 已接体重） |
| `references/coros-official-mcp-weight.md` | **COROS 官方 MCP 拉体重的 OAuth 流程 + cron 接入（非官方 API 无体重）** |
| `references/12week-plan-2026.md` | 你的真实 12 周半马计划 |
| `references/daily-report-template.md` | 日报模板 + 自动检查清单 |
| `references/cron-cache-fallback.md` | **cron/无头环境实时同步失败时的缓存聚合回退**（load_cache 不满足多日窗时如何重建 7 天窗）|
