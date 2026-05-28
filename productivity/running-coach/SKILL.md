---
name: running-coach
description: 跑步教练 — 统一入口：COROS 数据获取 + 每日训练反馈 + 阶段性计划。服务于马拉松破3目标。
---

# Running Coach — 跑步教练

统一入口，整合了：
- **数据获取**：COROS 手表活动抓取
- **训练分析**：基于运动科学的训练评估
- **教练反馈**：每日训练日报 + 明日建议

---

## 用户档案（统一数据源，不要分散）

| 字段 | 值 |
|------|-----|
| 目标 | 2026年12月 马拉松破3（配速 4'15"/km） |
| 当前水平 | 10km 50min / 20km 1:44 → VDOT ≈ 46 |
| 目标 VDOT | 52（对应马拉松 2:59） |
| LTHR | 173 bpm |
| Max HR | 191 bpm |
| 静息心率 | 51 bpm |
| 体重 | 71 kg |
| 身高 | 177 cm |
| 设备 | COROS PACE 3 |
| 时间约束 | 每天 8:20 前完成跑步 |

**COROS 账号**：`wangsiji@buaa.edu.cn` / `1993wang123704`

---

## 心率训练分区（LTHR 173 bpm）

| 区域 | 名称 | 心率范围 | 配速体感 |
|------|------|---------|---------|
| E | 轻松跑 | 129–142 bpm（74–82% LTHR）| 可以说话 |
| M | 马拉松配速 | 155–163 bpm（90–94% LTHR）| 稍吃力 |
| T | 乳酸阈值 | 163–168 bpm（94–97% LTHR）| 吃力但稳定 |
| A | 亚索 | 169–173 bpm（98–100% LTHR）| 接近极限 |
| I | 间歇 | 174–185 bpm（101–107% LTHR）| 非常吃力 |
| R | 冲刺 | > 185 bpm | 最大努力 |

---

## 核心训练原则

### 极化训练（80/20）
- 80% 训练量在 E 区
- 20% 在 T/I/R 区
- M 区不作为日常训练区

### "灰色区"训练陷阱（重点）
- 轻松跑误入 M 区（心率 > 142bpm）是基础期最常见的错误
- 危害：既没积累有氧基础（E区的效果），又没达到刺激阈值（T区以上的效果）
- 典型表现：6'00"/km 左右配速、心率 145–155bpm、感觉"不轻松也不吃力"
- 纠正方法：果断降速到 6'30"–7'00"/km，哪怕配速看起来很慢，只要心率在 E 区就是进步
- 恢复跑误入M区更严重——失去恢复效果还增加疲劳积累

### 10% 规则
- 每周跑量增幅不超过 10%
- 连续两周增负荷后需一周减量

### 48小时恢复原则
- 高强度训练后至少48小时才能再次高强度
- ST 次日不能跑阈值，阈值次日不能跑 ST

### 连续高强度禁止
- ST 和 T/LT 不能连续两天
- 长跑（>16km）次日必须休息

### 每周高强度上限：2次

---

## 周期训练阶段

```
基础期   5月–6月   有氧基础      周量 45–65km   E跑+1次短ST
建设期   7月–8月   阈值+速度     周量 65–85km   LT+ST+长E
巅峰期   9月–11月  马拉松配速专项 周量 85–105km  M配速长跑+I/LT维持
减量期   12月      恢复+状态调动 周量 50–70km   轻量M跑+休息
```

---

## 里程碑体系

| 里程碑 | 截止 | 任务 | 目标 |
|--------|------|------|------|
| M1 | 5月底 | 10km 测试 | < 48'00"（VDOT≥47） |
| M2 | 7月底 | 12km 阈值测试 | 均速 < 4'50"/km |
| M3 | 8月底 | 半马比赛 | < 1:38'00" |
| M4 | 10月中 | 30km @ 4'15"不掉速 | 掉速 ≤ 12秒/km |
| M5 | 11月底 | 赛前 30km 模拟 | 掉速 < 15秒/km |

---

## 每日训练反馈模板

```
🏃 教练日报 | {日期} {星期}
🌙 昨日睡眠：{睡眠时长}（目标 ≥ 7h）⚠️ 数据来源不可靠，待验证

━━━━━━━━━━━━━━━━━━━━━━
🎯 里程碑进度：{当前里程碑名称}
   目标：{具体目标值}
   截止：{日期}（还剩X天 / 已完成）
   当前状态：{达标/进行中/落后}
━━━━━━━━━━━━━━━━━━━━━━

【今日训练】
- {运动名称}
- 距离：{X} km | 配速：{X'XX"} | 平均心率：{X} bpm
- 训练负荷：{TL}

📊 本周数据（Mon–Sun）
- 累计跑量：{X} km / {X}次
- 累计负荷：TL {X}
- 较上周（Xkm）：{+/-X%} {↑/↓}

💬 训练点评
{客观数据点评}

📅 明日建议（{星期}·{类型}）
{具体训练内容和理由}
```

---

## 明日建议规则（强制）

1. **今日有 ST** → 明日必须休息或极轻 E 跑（≤30min）
2. **今日有 T/LT** → 明日休息或 30min 极轻松 E 跑
3. **今日长跑 >16km** → 明日必须休息
4. **连续两天高强度** → 绝对禁止
5. **每周高强度 >2次** → 不允许
6. **每周休息日** → 至少 1–2 天完全休息

---

## 数据获取

> **COROS API 详细文档**：`references/coros-api.md`（含睡眠接口、认证方式、已知陷阱）

**两个脚本并存，注意区分：**
- `/home/wangsiji/projects/running-page/sync_coros.py` — 项目目录，较慢，60s 内常超时
- `/home/wangsiji/.hermes/skills/productivity/running-coach/scripts/running_coach.py` — skills 目录，登录跳转处理正确，更可靠

**优先使用 skills 目录的脚本。**

### 脚本已知问题

**语法校验**：`scripts/running_coach.py` 从 Obsidian 导出时偶尔包含编码转义问题（如 `\\\"` 替代 `"` 或 `\\\"\\\"\\\"` 替代 `"""`）。首次运行前应验证语法：
```bash
python3 -c "import py_compile; py_compile.compile('~/.hermes/skills/productivity/running-coach/scripts/running_coach.py', doraise=True)"
```

如遇 `SyntaxError: unexpected character after line continuation character`，检查 docstring 和字符串字面量是否被转义，用 `sed` 修复或手动替换。

### 教练点评增强（对脚本输出的补充）

`running_coach.py --daily-report` 会自动生成基础日报，但助手应在此基础上补充：
1. **周训练一览表** — 展示本周所有训练记录的表格，帮助发现模式问题
2. **"灰色区"分析** — 当E区占比低时，解释为什么M区漂移对基础期有害
3. **里程碑测试周计划** — 当里程碑 ≤14天时，给出具体的倒计时训练安排
4. **恢复跑执行评价** — 明确标注恢复跑是否在E区（红/绿灯）

> **注意**：`~/projects/running-page/` 目录可能不存在，但 running_coach.py 脚本不依赖它——它独立运行并缓存到 `~/.hermes/coros-cache/`。

```python
import sys
sys.path.insert(0, '/home/wangsiji/.hermes/skills/productivity/running-coach/scripts')
from running_coach import fetch_activities
from datetime import datetime, timedelta
date_to = datetime.now().strftime('%Y-%m-%d')
date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
acts = fetch_activities(date_from, date_to, headless=True)
```

### 睡眠数据 ⚠️

**已知问题**：COROS `dashboard/queryCycleRecord` API 返回的睡眠数据是缓存值，91天历史数据完全相同，不可用于趋势追踪。type=16 不是总睡眠时长，App 显示值与任何单一 type 字段都无法匹配。详见 `references/coros-api.md`。

**当前状态**：sleep.json 数据不可靠（API返回缓存值，91天完全相同），需用户配合截图 COROS App 睡眠详情页验证字段含义。**让用户直接口述/打字数值**，vision 工具响应不稳定。

**数据文件**：`/home/wangsiji/projects/running-page/data/sleep.json`（字段：date, sleep_sec, sleep_str, types）

```bash
# 拉取全量活动+睡眠数据
cd /home/wangsiji/projects/running-page && python3 sync_coros.py

# 仅拉睡眠数据（跳过跑步）
python3 sync_coros.py --sleep-only
```

输出文件：`/home/wangsiji/projects/running-page/data/activities.json`

**数据字段**：`id`, `date`（YYYYMMDD）, `display_date`（YYYY-MM-DD）, `sport`, `dist_km`, `pace_sec`, `pace_str`, `duration_sec`, `duration_str`, `hr_avg`, `hr_zone`（E/M/T/A/I）, `tl`

**近7天数据读取示例**：
```python
import json
from datetime import datetime, timedelta

with open('/home/wangsiji/projects/running-page/data/activities.json') as f:
    data = json.load(f)

today = datetime(2026, 5, 2)
cutoff = today - timedelta(days=7)
recent = [a for a in data if datetime.strptime(a['date'], '%Y%m%d') >= cutoff]
recent.sort(key=lambda x: x['date'], reverse=True)
```

**备用缓存数据**：`/home/wangsiji/.hermes/coros-cache/YYYY-MM-DD.json`（每日抓取缓存）

### 数据获取：使用 skill 内的 `running_coach.py`（不是 `sync_coros.py`）

**⚠️ 已知问题**：`sync_coros.py`（在 `projects/running-page/` 下）登录后等待 redirect 会超时（约60s），COROS 页面加载慢导致流程挂住。

**正确方式**：使用 skill 内置的 `scripts/running_coach.py`，它在 Playwright 内通过 `page.evaluate` + captured token 直接调 COROS API，全流程约55秒稳定完成。无需 `cd` 到 `~/projects/running-page`。

```bash
python3 /home/wangsiji/.hermes/skills/productivity/running-coach/scripts/running_coach.py --days 7 --output /tmp/running_today.json
```

**日报生成前必做**（更新数据后生成）：
```bash
python3 /home/wangsiji/.hermes/skills/productivity/running-coach/scripts/running_coach.py --days 7 --daily-report
```

输出 `activities.json` 数据文件路径：`/home/wangsiji/projects/running-page/data/activities.json`（备用缓存 `~/.hermes/coros-cache/YYYY-MM-DD.json`）

sleep.json 数据不可靠（见上节），以用户口述为准。

### 雨天训练注意事项

用户提到"最近一直在下雨"。雨天跑步注意事项：
- 路面湿滑 → 降低配速 10-20 秒/km
- 鞋子排水 → 穿排水性好的鞋，避免棉质袜
- 视距缩短 → 穿亮色/反光装备
- 心率可能偏低 → 以体感为准，不强求配速
- 感冒风险 → 及时擦干换衣

日报模板可加一行：`🌧️ 今日天气：雨天（注意防滑、及时换衣）`
### 输出格式

```json
{
  "fetched_at": "2026-04-30T10:46:13",
  "date_from": "2026-04-24",
  "date_to": "2026-04-30",
  "count": 7,
  "activities": [
    {
      "date": "今天",
      "sport": "8k轻松跑+6ST",
      "dist": "10.58km",
      "dist_km": 10.58,
      "duration": "01:03:56",
      "pace": "06'00\"",
      "pace_sec": 360,
      "hr": 149,
      "hr_zone": "M区",
      "tl": 117
    }
  ]
}
```

---

## Cron 自动化

每日早上 8:20 自动推送训练日报：

```
cron job: daily-running-report
时间: 20 8 * * *
deliver: origin
skills: running-coach
```

**⚠️ 数据时效性：日报生成前必须重新拉取数据**

COROS 登录偶尔很慢（可达 40–50 秒），60s 内可能超时。如报告数据不全，多试一次即可。

**日报生成前必做**：
```python
import sys
sys.path.insert(0, '/home/wangsiji/.hermes/skills/productivity/running-coach/scripts')
from running_coach import fetch_activities
from datetime import datetime, timedelta
date_to = datetime.now().strftime('%Y-%m-%d')
date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
acts = fetch_activities(date_from, date_to, headless=True)
```

任务 prompt 核心逻辑：
1. 调用 `running_coach.py` 的 `fetch_activities` 获取最近7天数据
2. 分析今日训练（最近一条）
3. 按模板生成日报
4. 根据训练类型 + 48h规则给出明日建议
5. 标注当前里程碑进度

---

## 📋 训练日报自动检查清单

生成日报时，**必须**自动检查以下各项并体现在"训练点评"和"数据分析"区块中：

### 80/20 极化训练合规检查
- 计算本周E区TL占比（E区TL ÷ 总TL × 100%）
- 目标：> 80%
- 低于50%：⚠️ 严重警告 + "灰色区训练"分析
- 50–70%：⚠️ 提示未达标
- 70–80%：✅ 接近目标

### 周训练一览表
- 在日报"数据分析"区块中，添加本周每天的汇总表（日期、内容、距离、配速、心率、区、TL）
- 用表格一目了然展示训练结构，方便发现模式问题（如连续高强度、M区漂移）
- 格式示例：
```
| 日期 | 内容 | 距离 | 配速 | 心率 | 区 | TL |
|------|------|------|------|------|----|----|
| 5/18 | 恢复跑 | 6.27km | 8'01" | 135 | E | 36 |
| 5/19 | 🔴 10k轻松跑 | 10.95km | 6'11" | 148 | M | 111 |
```

### 连续跑步天数检查
- 从当天往前数，统计连续有活动的天数
- ≥4天 → 强制建议休息
- 3天 → 建议E跑或休息
- 已有脚本函数 `consecutive_run_days_check()`

### 轻松跑M区漂移检测
- 活动名称含"轻松跑"或"恢复跑"但心率区=M区 → 警告跑太快
- E区上限142bpm（LTHR 74–82%）
- 常见原因：配速太快、没控制心率、手表测HR偏高

### 里程碑倒计时检查
- 计算当前里程碑截止日期的剩余天数
- 剩余 ≤ 14天 → 标记"⏰"紧急
- 剩余 ≤ 14天 → 同时生成**里程碑测试周计划**（TODO 清单）
  ```
  以M1（10km测试）为例，测试通常安排在周六/日：
  测试前7天安排：
  D-7（周六）休息
  D-6（周日）E区跑8km
  D-5（周一）休息
  D-4（周二）E区跑8km + 短冲刺3×100m
  D-3（周三）E区跑6km
  D-2（周四）休息
  D-1（周五）赛前激活：3km E跑 + 3×200m加速跑
  D-Day（周六）测试！
  ```
- 剩余 ≤ 7天 → 给出具体安排建议
- 已过期 → 标记为需更新里程碑

### 高强度训练间隔检查
- 检查昨日是否有高强度（I/A/T区 或 TL>100）
- 如果有且今日又是高强度 → 标记违规
- 参考48h恢复原则

