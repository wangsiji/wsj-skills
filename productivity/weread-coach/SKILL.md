---
name: weread-coach
description: 微信读书教练 — 每日阅读反馈 + 知识卡片生成。基于微信读书账号的阅读数据，分析阅读习惯，生成阅读日报。
---

# Weread Coach — 微信读书教练

每日阅读反馈 + 知识卡片生成。分析阅读习惯，追踪阅读进度，生成阅读日报。

---

## 用户档案

| 字段 | 值 |
|------|-----|
| 读书时间 | 每天 20:00–22:00 带娃睡觉时（约 2 小时） |
| 目标 | 积累知识，建立卡片盒笔记体系 |
| 知识卡片目录 | `/home/wangsiji/projects/knowledge/cards/` |

---

## 核心功能

1. **每日阅读日报** — 分析昨日阅读内容，给出反馈
2. **知识卡片生成** — 从当日高亮/笔记自动生成卢曼卡片
3. **阅读习惯追踪** — 连续阅读天数、每周阅读量、书籍类型分布

---

## 数据获取

### 认证方式

微信读书需要登录态，使用 Cookie 认证。

**从浏览器导出 Cookie（推荐）**：
1. 在 Chrome/Firefox 登录 [weread.qq.com](https://weread.qq.com)
2. 安装 **EditThisCookie** 扩展，导出 Cookie 为 JSON
3. 运行：
```bash
python3 ~/.hermes/skills/productivity/weread-coach/scripts/weread_coach.py \
  --cookie-file /path/to/cookies.json
```

**Cookie 重建逻辑**：
- 导出的 Cookie 通常缺少 `wr_sid`，但有 `wr_vid` 和 `wr_rt`
- `wr_sid = wr_vid + "_" + URL解码(wr_rt)`
- 脚本会自动重建并保存

### 数据 API

| API | 说明 |
|-----|------|
| `GET https://weread.qq.com/api/user/notebook` | 书架数据（可用，无需特殊认证） |
| `GET https://i.weread.qq.com/shelf/sync` | 需要 wr_sid 认证 |
| `GET https://i.weread.qq.com/review/list` | 书籍笔记，需要 wr_sid 认证 |

> ⚠️ `i.weread.qq.com` 需要完整的 `wr_sid` cookie（格式 `userVid_sessionId`），而 `weread.qq.com` 的 web API 通常只需基础 cookie 即可访问。

关键 Cookie：
- `wr_vid` — 用户 ID
- `wr_sid` — 格式 `{wr_vid}_{sessionId}`，可从 `wr_rt` 解码重建
- `wr_skey` — 认证签名
- `wr_rt` — 编码后的 session，URL 解码后即 sessionId

### Cookie 重建源码

```python
def rebuild_wr_sid(cookies):
    cookie_dict = {c['name']: c for c in cookies}
    if 'wr_sid' in cookie_dict:
        return  # 已存在

    if 'wr_vid' in cookie_dict and 'wr_rt' in cookie_dict:
        import urllib.parse
        user_vid = cookie_dict['wr_vid']['value']
        session_id = urllib.parse.unquote(cookie_dict['wr_rt']['value'])
        wr_sid_value = f"{user_vid}_{session_id}"
        cookies.append({
            'name': 'wr_sid',
            'value': wr_sid_value,
            'domain': '.weread.qq.com',
            'path': '/',
        })
```

### 数据格式

```json
{
  "synckey": 1777585905,
  "totalBookCount": 119,
  "books": [{
    "bookId": "3300048761",
    "book": {
      "title": "鱼不存在",
      "author": "露露·米勒",
      "cover": "https://..."
    },
    "readingProgress": 45,
    "noteCount": 12,
    "reviewCount": 1,
    "sort": 1745961600
  }]
}
```
- `sort` 字段是 Unix 时间戳（秒），表示最后阅读时间
- `readingProgress` 是百分比（0-100）

---

## 每日阅读日报模板

```
📖 读书日报 | {日期} {星期}

━━━━━━━━━━━━━━━━━━━━━━
【昨日阅读】
- 书名：《{书名}》
- 作者：{作者}
- 阅读进度：{X}% → {Y}%
- 章节：{章节名}

【今日高亮】
"{划线内容}"
  — {书名} P.{页码}

【阅读洞察】
- 阅读时长：约 {X} 分钟
- 划线 {X} 条 / 笔记 {X} 条
- {分析文字}

【明日建议】
{明日阅读建议，基于当前阅读进度和主题}
━━━━━━━━━━━━━━━━━━━━━━
```

---

## 知识卡片格式

文件名：`{YYYY-MM-DD}-{核心概念}.md`

```markdown
# {核心概念}

## 核心观点
{从高亮中提炼的核心观点，1-2句话}

## 个人体验
{结合自身经历的解读，1-2段落}

## 行动指引
- {具体的下一步行动}
- {第二个行动}

## 参考资料
{作者}.《{书名}》. {出版社}, {年份}. 第{X}页.
```

---

## Cron 自动化

每日早上 08:30 自动推送阅读日报：

```
时间: 30 8 * * *
deliver: origin
skills: weread-coach
```

任务流程：
1. 读取昨日阅读数据（`~/.hermes/weread_data/weread_{昨天日期}.json`）
2. 如果有新阅读内容，生成阅读日报
3. 如果有高质量划线，生成知识卡片
4. 通过 Telegram 发送日报
5. 知识卡片保存到 `/home/wangsiji/projects/knowledge/cards/`

---

## 已知限制

1. **Cookie 有效期**：微信读书 Cookie 长期不登录会失效（约 30 天），需定期刷新
2. **API 限流**：高频请求可能触发限流，脚本内置重试机制
3. **书籍内容**：API 只返回元信息和笔记，不返回书籍正文内容
4. **服务器环境**：无法扫码登录，必须从浏览器导入 Cookie
