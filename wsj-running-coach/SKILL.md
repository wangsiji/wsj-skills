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

1. 减重是破三最高杠杆（1kg≈3秒/km，158→125斤≈释放50秒/km）
2. 每次执行前拉最新 COROS 数据，不用缓存
3. vault 是真相源，skill 用户核心数据段为快照（过期不更新不代表目标变）
4. 睡眠/HRV 从 coros-mcp mobile API 自动获取，失败退口述
5. 体重手表不测，需口述或 Apple Health 导出

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
用户说"里程碑进度"
  → 查当前里程碑 → 进度报告 → 读 vault 年底三目标训练总表
用户说"睡眠/HRV/体重"
  → 睡眠/HRV → coros-mcp get_sleep_data/get_daily_metrics
  → 体重 → 用户口述（手表不测）
```

## 输入输出协议

**输入**：用户自然语言指令（训练反馈/测试/调整）
**输出**：日报模板 + 明日建议 + vault 运动周追踪表写入指引

## Pre-flight Check

- [ ] COROS 数据已拉最新（running_coach.py or coros-mcp）
- [ ] vault 健康主线已确认（10-健康.md + 年底三目标训练总表.md）
- [ ] 睡眠数据已取（coros-mcp get_sleep_data）
- [ ] 用户核心数据段标注过期风险

## Never Do

- ❌ 用缓存 COROS 数据（每次必须拉最新）
- ❌ 用 read_file() 读后直接写回 vault（行号污染）
- ❌ 内联密码（凭证从环境变量/keyring）
- ❌ 用 Web API dashboard/query 的 sleep 字段（缓存值，不可用）
- ❌ 在建设期（7-8月）安排全马测试（打乱巅峰期节奏）

## 引用导航

| 文件 | 何时读 |
|------|--------|
| `references/heart-rate-zones.md` | 心率分区 + 灰色区判断 |
| `references/running_general.md` | 80/20、配速、伤防理论底座 |
| `references/vdot-prediction.md` | VDOT 预测表 + 训练进步因子 |
| `references/screenshot-parsing.md` | COROS 截图 OCR 解析 |
| `references/coros-api.md` | COROS API 端点细节 |
| `references/coros-mcp.md` | coros-mcp 安装/cron限制 |
| `references/tooling-details.md` | 程序化调用代码片段 |
| `references/body-composition.md` | 体重数据说明（COROS 不测） |
| `references/12week-plan-2026.md` | 你的真实 12 周半马计划 |
| `references/daily-report-template.md` | 日报模板 + 自动检查清单 |
