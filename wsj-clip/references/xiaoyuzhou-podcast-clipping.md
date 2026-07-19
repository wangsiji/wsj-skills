# 小宇宙播客剪藏

## 适用场景

用户发来 `xiaoyuzhoufm.com` 链接时使用。

## 完整流程

与 Method A 的并行模式不同，小宇宙没有独立原文提取（浏览器/show notes 即原文），只需一轮 getnote。

### 步骤 1：浏览器获取节目信息 + Show Notes

```bash
# 浏览器打开页面
browser_navigate(url="https://www.xiaoyuzhoufm.com/episode/<ID>")

# 展开 Show Notes（关键！页面默认折叠）
browser_click(ref="@e54")  # 或 region "节目show notes" 内的可点击元素
browser_snapshot(full=true)
```

从页面提取：
- **标题**（h1）
- **播客名**（如"长谈·脱不花"）
- **时长**（如"174分钟"）
- **播放量**
- **Show Notes**（展开后的完整内容，含嘉宾介绍、时间轴）

### 步骤 2：提交 getnote（并行启动）

```bash
curl -X POST "https://openapi.biji.com/open/api/v1/resource/note/save" \
  -H "Authorization: $GETNOTE_API_KEY" \
  -H "X-Client-ID: $GETNOTE_CLIENT_ID" \
  -H "Content-Type: application/json" \
  -d '{"note_type": "link", "link_url": "<小宇宙URL>", "tags": ["播客剪藏"]}'
```

返回中取 `data.tasks[0].task_id`（注意是数组，不是 `data.task_id`）。

### 步骤 3：轮询进度（POST！不是 GET）

```bash
curl -s -X POST "https://openapi.biji.com/open/api/v1/resource/note/task/progress" \
  -H "Authorization: $GETNOTE_API_KEY" \
  -H "X-Client-ID: $GETNOTE_CLIENT_ID" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id>"}'
```

轮询间隔：15-30s。

### 步骤 4：取转写稿

拿到 `note_id` 后调详情接口（**GET + ?id=**，不是 `?note_id=`）：

```bash
curl -s -X GET "https://openapi.biji.com/open/api/v1/resource/note/detail?id=<note_id>" \
  -H "Authorization: $GETNOTE_API_KEY" \
  -H "X-Client-ID: $GETNOTE_CLIENT_ID"
```

取 `data.note.web_page.content` 字段，这是带时间戳的完整逐字稿。

⚠️ **关键规则**：即使 `data.note.content` 为空（AI 总结尚未完成），`web_page.content` 通常仍包含完整转写稿。不要因为 `content=""` 就放弃。

### 🕐 步骤 4.5：长音频等待 AI 总结（超长内容专用）

对于超长播客（60 分钟以上），getnote AI 总结需要额外处理时间。

**典型时间线：**
- 提交后 30s~2min → `web_page.content` 已有完整转写稿（语音识别完成）
- 提交后 3~8min → `data.note.content` 才出现 AI 总结

**不要犯的错：**
首轮轮询看到 `status=processing` + `content=""` + `error_msg="生成笔记失败"` 就宣布"AI 总结不可用" → **会被用户纠正**。转写稿已有不等于总结已出。

**正确做法：**
1. 首轮拿到 `note_id` 后，先取 `web_page.content`（转写稿通常已有）
2. 如果 `content=""`，**设 cron 任务 5 分钟后复查**（cronjob action=create schedule=5m），不阻塞当前流程
3. cron 任务里再调 `/note/detail?id={note_id}`，看 content 是否有内容
4. 有内容（>50 chars）→ 更新原文件插入 AI 总结；仍为空 → 再等 3 分钟复查

#### Cron 任务结构（参考）

创建 cron 任务时，在 prompt 中包含以下信息：

```
检查 getnote 的 AI 总结是否已生成。

参数：
- task_id: <从 save 响应获取>
- note_id: <从轮询响应获取>
- 文件路径: <00-LLM-WiKi/Raw/小宇宙_xxx.md>

步骤：
1. 调 GET /open/api/v1/resource/note/detail?id={note_id}，Authorization 用 $GETNOTE_API_KEY
2. 检查 data.note.content 是否非空（>50 chars）
3. 如果有内容，读原文件，在 "## 节目信息" 前插入 "## AI 智能总结\n\n{content}\n\n"，
   同时移除文件顶部可能存在的 "⚠️ AI 总结待生成" 提示行
4. 告知结果：「EPXX AI 总结已生成并更新到文件」或「AI 总结仍未生成，再等 3 分钟」

文件标记约定：首次保存时在标题下方添加 `> ⚠️ AI 总结待生成：已提交 getnote 处理，5 分钟后自动复查更新。`
cron 复查时移除这一行，替换为实际的 `## AI 智能总结` 段落。
```

#### 文件更新逻辑（cron 任务执行）

```python
# 获取 AI 总结
content = detail_resp['data']['note']['content']
if not content or len(content.strip()) <= 50:
    print("AI 总结仍未生成，再等 3 分钟")
    # cron 任务会自动重试，不需要额外操作

# 读原文件
with open(filepath) as f:
    text = f.read()

# 替换 "⚠️ AI 总结待生成" → 插入 AI 总结段落
old = '> ⚠️ AI 总结待生成：已提交 getnote 处理，5 分钟后自动复查更新。\n\n## 节目信息'
new = f'## AI 智能总结\n\n{content}\n\n## 节目信息'
text = text.replace(old, new)

with open(filepath, 'w') as f:
    f.write(text)
```

#### Cron 任务交付物规范

cron 任务的最终响应会被自动投递到用户的聊天中，格式要求：
- **总结已生成**：「EPXX AI 总结已生成并更新到文件」+ 简要说明（字符数、文件大小）
- **总结仍未生成**：「AI 总结仍未生成，再等 3 分钟」— cron 会自动重试，无需手动干预
- **静默**：如果 cron 任务发现无需操作（已处理过），输出 `[SILENT]` 抑制投递

### 步骤 5：合并保存

合并 Show Notes + 完整转写稿到一个文件，保存到 `00-LLM-WiKi/Raw/`。

文件名格式：`小宇宙_{作者}_{标题}.md`

```python
from hermes_tools import write_file

merged = f"""---
category:
  - "[[小宇宙]]"
author:
  - "[[{host_name}]]"
url: "{url}"
tags: [剪藏, 播客]
created: {today}
modified: {today}
---

# {title}

## 节目信息

- **播客：** {podcast_name}
- **嘉宾：** {guests}
- **时长：** {duration}
- **播放量：** {play_count}
- **来源：** [小宇宙]({url})

## Show Notes

{show_notes_text}

## 完整转写稿

{transcript_body}
"""

write_file(filepath, merged)
```

### 步骤 6：验证

```bash
ls -lh "00-LLM-WiKi/Raw/小宇宙_*.md"
```

确认文件存在且大小合理（2h+ 播客转写稿通常 >50KB）。

## 已知陷阱

| 问题 | 处理 |
|------|------|
| `/task/progress` 返回 404 | 用的是 GET？改成 POST 带 JSON body |
| `/note/detail` 返回"参数错误" | 参数是 `?id=` 不是 `?note_id=` |
| `content` 为空（AI 总结失败） | 不放弃，用 `web_page.content` 取转写稿 |
| `error_msg="生成笔记失败"` | 忽略，以 status 为准，detail 可能已有内容 |
| 页面 Show Notes 不可见 | 必须 `browser_click` 展开，页面默认折叠 |
| 转写稿含 `[OUTPUT TRUNCATED]` | 页面的内容截断了，getnote 通常返回完整稿 |
