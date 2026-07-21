---
name: wsj-running-coach
description: 健康管家+跑步教练：每日定时（cron 10:00）向第二大脑同步跑步/俯卧撑/体重/睡眠四类 COROS 数据；并当用户问训练反馈/测试/比赛/配速/破三进度时拉 COROS 数据生成教练日报，服务全马破三(<3:00)。
version: 2.0.1
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
4. 睡眠/HRV 从 coros-mcp mobile API（`fetch_sleep` / `get_daily_metrics`）自动获取，失败退口述。⚠️ **`fetch_sleep` 必须 mobile token**：`try_auto_login()` 文档明确「Always skips mobile login」只拿 web token，直接调 `fetch_sleep` 会触发 `_ensure_mobile_token(auth)` → `auth.mobile_access_token` 报 `NoneType`。修正：调用前显式 `await login_mobile(email, password, "cn")` 补 mobile token（web 偶发失败时 mobile 仍稳，可作兜底）。睡眠日期 `SleepRecord.date`（= `happenDay`）是 `YYYYMMDD`（无横杠，**醒来日**，**非入睡日**）；cron 拉 `prev_y..d_y` 区间得每天一条，每条按**自身 date** 落对应日期行，绝不可统一写进 `day_str` 行（否则错位+漏写，实测踩过）。细节见 `references/coros-sleep-sync.md`
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
- ❌ 把跑步/俯卧撑/训练计划迁到官方 MCP：动态注册的 public client 被官方网关限流，`querySportRecords`/`queryTrainingSchedule` 等运动记录类 tool 调不通（返回 "exceeds the LLM capability boundary"）。体重走官方 MCP（queryUserInfo），运动记录/计划走非官方 coros-mcp，这是当前最优分工，勿反复试迁移。详见 `references/coros-official-mcp-weight.md` 的「官方 MCP 能力边界」
- ⚠️ `running_coach.py` 当前硬编码密码（违反上条「内联密码」）；cron 自动跑前先确认 playwright 可用。CLI 参数用 `--from-date`/`--to-date`（非 `--date-from`）

## 每日自动拉取（cron 模式）

- **健康管家主通道**：`~/.hermes/scripts/cron_sync_coros.py`（每天 10:00 cron 跑），一次性拉跑步/俯卧撑/体重/睡眠四项并写 `01-Projects/Routine/` 下四个数据文件 + 发日报。这是生产路径，勿用 Playwright 版跑日常同步（慢且偶发超时）。
- 临时手动触发：`python3 /home/wangsiji/.hermes/scripts/cron_sync_coros.py`
- Playwright 版 `scripts/running_coach.py --from-date <昨天> --to-date <今天> --daily-report` 仅作教练日报/兜底（无头回退见下），不作为日常同步入口。
- 用户说「每天拉训练/同步数据」：确认 10:00 cron 在（job 名「每日 COROS 训练同步（健康管家）」），不在就按「cron 脚本落地规则」重建。

### cron 脚本落地规则（实测踩坑，2026-07-20 重建确认）

- **cron 的 `script` 字段必须放在 `~/.hermes/scripts/` 下**，只写文件名（如 `script: cron_sync_coros.py`）。给绝对路径或 vault/skills 内路径会被拒：`Script path must be relative to ~/.hermes/scripts/`；用**软链接**也会被校验拒绝（resolve 后真实路径在 skills 目录，判为 escape）。→ **真实脚本必须实体存在于 `~/.hermes/scripts/`**；版本管理副本放 `~/.hermes/skills/custom/scripts/cron_sync_coros.py`（改完 `cp` 过去同步，勿指望软链）。
- **可用脚本**：`~/.hermes/scripts/cron_sync_coros.py`（job 名「每日 COROS 训练同步（健康管家）」，每天 **10:00**）。它走 **coros-mcp 程序化拉取**（非 Playwright），按 `sport_type`/`name` 区分跑步与俯卧撑，分别 `append_row` 进 `跑步数据.md` / `俯卧撑数据.md`；体重走 **官方 MCP**（`coros_weight.get_weight_kg()`，子进程调用，写 `体重数据.md`，同日去重）；**睡眠走 `coros_api.fetch_sleep`（mobile API，需显式 `login_mobile` 补 token）写 `睡眠数据.md`**。四项同日去重，无活动日输出「无 COROS 活动记录」不写库。详见 `references/coros-official-mcp-weight.md`（体重）与 `references/coros-sleep-sync.md`（睡眠）。\n\n⚠️ **跑步数据表头（2026-07-20 起）**：11 列 `| 日期 | 开始时间 | 距离(km) | 时长 | 平均配速 | 配速区间 | 平均HR | 心率区间 | 训练负荷 | 来源 | 备注 |`。开始时间/时长/配速/配速区间/心率区间来自 `fetch_activity_detail`（activity_list 列表接口缺这些字段）。详情：`summary.startTimestamp`（**毫秒！非秒 → 改用 list 的 `startTime`）→`HH:MM`、`summary.totalTime`（厘秒 1/100s→`// 100`→秒→`mm:ss`）、配速由 `dur_s / dist_m * 1000` 算、`zoneList[type=126]` 心率区间（`zoneIndex 0-5`→`E/M/HV/VO2/A/I`，按 `percent` 拼如 `E 28% M 71%`，注意有空格）、`zoneList[type=130]` 配速区间（`Z0/Z1/Z2...` 前缀 + 空格 + `%`）。历史行保持旧格式不重写。详见 `references/coros-api-quirks.md`。\n\n⚠️ **`pull_day` 内嵌子进程脚本的 f-string 嵌套陷阱**：`script = f'''...'''` 的外层 f-string 会**先处理自己** `{...}` 表达式，所以内嵌子进程脚本中含 `f"{name}{pct}%"` 或 `f"{m}:{sec:02d}"` 时，`{name}`/`{m}`/`{sec}` 会被外层的 f-string 解析器在外层作用域查找 → `NameError`。解决：外层 f-string 内的内嵌子进程脚本中**禁用 f-string**，用字符串拼接（`name + str(pct) + "%"`、`str(m) + ":" + str(sec).zfill(2)`）。\n\n⚠️ **`totalTime` 单位厘秒**：COROS activity detail summary 的 `totalTime` 单位是**厘秒（1/100 s）**（非毫秒）。转换秒 → `int(dur_raw) // 100`。`it.get("totalTime")`（activity_list）直接返回秒，`s.get("totalTime")`（activity detail）返回厘秒。`or` 链优先取第一个 truthy，若 summary 有值必定先取厘秒 → 不能硬 `// 1000` 否则少数量级。\n\n⚠️ **双文件同步**：cron 真实运行件在 `~/.hermes/scripts/`，git 版本管理副本在 `~/.hermes/skills/custom/scripts/cron_sync_coros.py`。`cron_sync_coros.py` 不在 wsj-running-coach/scripts/ 内部，而是顶层 shared scripts/。改完 `cp` 同步两份，commit 时只管 skills 那份。**软链接不可用**（cron 校验 resolve 到 git 路径判为 escape 拒）。
- **重建 cron 的方法**（本会话踩坑：调用 `cronjob(action='update')` 带错 job_id 会让整个 list 丢失 818beb975a1f、b68db8e893a9 等 job！）：丢 job 后直接 `cronjob(action='create', name=…, schedule='0 10 * * *', script='cron_sync_coros.py', prompt='每天10:00执行 cron_sync_coros.py 拉取跑步/俯卧撑/体重/睡眠写入第二大脑各数据文件并发回日报')` 重建即可（create 返回新 job_id）。23:00 提交 vault 的 cron 同样用 create 重建，script=`daily_vault_commit.sh`，prompt 跑 `bash /home/wangsiji/.hermes/scripts/daily_vault_commit.sh`。
- 复用 `running_coach.py` 内联密码重登（env 为空时）；子进程 `-c` 内嵌脚本务必 `import datetime`（否则空 stdout 时 `[-300]` 索引报错）。`__pycache__` 会缓存旧版内嵌脚本逻辑，改完务必 `rm -rf /home/wangsiji/.hermes/scripts/__pycache__` 再测。
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
| `references/coros-sleep-sync.md` | **COROS 睡眠同步：`fetch_sleep` 需 mobile token + `SleepRecord.date` 为 YYYYMMDD 无横杠 + 字段映射 → 睡眠数据.md** |
| `references/github-upstream-pr.md` | **把本地改动提 PR 回上游仓库的可复用流程**（fork→分支→push→gh pr create，自包含要求+PR body 写法）；coros_weight.py 即 PR #46 到 cygnusb/coros-mcp |
| `references/coros-api-quirks.md` | **COROS API 字段格式陷阱**（startTimestamp 毫秒、totalTime 厘秒、zoneList type 126=HR/130=pace、`fetch_activity_detail` 使用模式、nested f-string 嵌套错误） |
| `references/gh-pr-edit-quirks.md` | **`gh pr edit --title/--body` 被 Projects classic 警告静默吞 → 改用 `gh api -X PATCH /repos/<o>/<r>/pulls/<N>`**（上游 PR 编辑可靠路径，验证看 `gh pr view --json`） |
| `scripts/cron_sync_coros.py`（git 副本） | **健康管家每日同步主脚本**（真实运行件在 `~/.hermes/scripts/`，此为其版本管理副本；改完 `cp` 同步）。脚本内嵌子进程：外层 f-string 会解析 `{...}` → 内层禁用 f-string 用拼接；`totalTime` 厘秒 `//100` 而非 `//1000`）<br>**append_row 2026-07-21 修复**：①表头匹配 `startswith("| 日期")` 遇多空格对齐表头失败 → 改 `"|" in ln and "日期" in ln`；②去重原地替换不挪位（旧行在末尾）→ 改先删旧行再统一插入表头后；③尾部空行未剥离致断表 → `while pop()` 去空串。
| `references/12week-plan-2026.md` | 你的真实 12 周半马计划 |
| `references/daily-report-template.md` | 日报模板 + 自动检查清单 |
| `references/cron-cache-fallback.md` | **cron/无头环境实时同步失败时的缓存聚合回退**（load_cache 不满足多日窗时如何重建 7 天窗）|
