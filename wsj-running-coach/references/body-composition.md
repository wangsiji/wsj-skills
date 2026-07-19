---
name: body-composition
description: COROS不提供体重数据说明 + 体脂秤自动化探测结论与替代方案（Apple Health/口述）
---

## COROS 体重数据说明

**COROS PACE 3 手表不测量体重/体脂。COROS API 也不提供体重数据。**

2026-06-01 全面探测结论（通过 coros-mcp 逆向移动端 API）：
- **Web API**（`teamcnapi.coros.com`）：dashboard、analyse、dayDetail 共 50+ 字段 — 全部运动指标，无体重
- **Mobile API**（`apicn.coros.com`）：statistic 类型 1~100 全部探测，body/weight 路径模式 16 个 — 全部无数据
- **`/user/getUserWeight`** 返回 500
- 以上所有端点均不含 bodyWeight/bodyFat/weight/kg 等字段

当用户问"从高驰获取体重数据"时：
1. 直接告知 COROS 不提供此接口
2. 推荐**米家体脂秤 S400 + SmartScaleConnect**（扫码登录可获取精确体重+体脂）
3. 或用户直接从 COROS 手机 App 截图体重记录页

---

## 身体成分数据（体脂秤）

⚠️ **现状：暂无自动化方案，2026-06 全面探测后搁置。不要在不确认环境变化的情况下重试。**

体重/体脂是影响配速和恢复的重要指标。

### 已知工具与结果（2026-06 最终评估）

| 工具/方法 | 状态 | 原因 |
|-----------|------|------|
| SmartScaleConnect + 密码登录 | ❌ | Xiaomi API 返回 10025，需设备验证 |
| SmartScaleConnect + 扫码 | ❌ | 二维码指向国际版，中国区账号「地区不支持」 |
| micloud Python 库 | ❌ | 同样 70016 + 10025 |
| Playwright 自动化 SPA 登录 | ❌ | 新登录页仅显示国际社交登录（Facebook），无短信入口 |
| 米家 App 内提取 Token | ❌ | iOS 无开发者模式，无法获取 ServiceToken |
| COROS API（手表手动输入） | ❌ | COROS API 无体重字段（2026-06 全面探测，请勿重测） |
| Apple Health 导出 | ✅ 手动可行 | iPhone 健康 App → 导出 → 解析 zip 中 XML |
| 用户口述/截图 | ✅ 随时可用 | 最简单可靠，用户可用 Telegram 发送当前体重 |

### 操作指引

当用户问"能不能获取体重数据"时，**不要重复尝试以上已探明不可用的方案**。直接告知现状：
1. **Apple Health 导出** — 如果 COROS 同步了体重到健康 App
2. **直接告诉我** — 我帮记录和追踪趋势
3. 如果环境变化（新工具发布、Xiaomi API 更新），可重新评估
