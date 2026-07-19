# getnote API 通用规则（含 env 协作模式）

所有剪藏共享的 getnote 接入规则。执行剪藏前先读此文件。

## 端点

| 操作 | 方法 | URL | 参数 | Auth 要求 |
|------|------|-----|------|-----------|
| 提交 | POST | `/open/api/v1/resource/note/save` | `{"note_type":"link","link_url":"<URL>","tags":[...]}` | 宽松 |
| 轮询 | POST | `/open/api/v1/resource/note/task/progress` | `{"task_id":"<task_id>"}`（单数字符串） | 宽松 |
| 取详情 | GET | `/open/api/v1/resource/note/detail?id={note_id}` | `?id=` | 严格 — 裸 key，无 Bearer |

> ⚠️ `task_id` 在 `data.tasks[0].task_id`（数组里！）

## 关键规则

1. **忽略 error_msg** — 以 status + detail 实际内容为准
2. **不要被空 content 骗过** — `content=""` 时 `web_page.content` 通常有转写稿
3. **短内容秒出** — B站 < 10min，约 60s 就绪
4. **长内容需要时间** — 60min+ 播客首轮为空正常，设 cron 5min 复查
5. **早停条件**（仅网页/X 链接，非媒体）— 3min 无结果可跳过
6. **X 链接** — 成功率约 1/3 但必须尝试

## Auth 格式

```bash
curl -H "Authorization: $GETNOTE_API_KEY" -H "X-Client-ID: $GETNOTE_CLIENT_ID"
# detail 同上，裸 key，无 Bearer
```

> `$GETNOTE_API_KEY` 在 terminal curl 工作，在 execute_code 沙箱不可用。

## execute_code + terminal 协作模式

Step 1: `write_file` 写脚本到 `/tmp/`
```python
# execute_code 沙箱无 env，通过 terminal 继承
with open('/tmp/getnote_detail.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
import os, urllib.request, json
note_id = "..."
req = urllib.request.Request(
    f"https://openapi.biji.com/open/api/v1/resource/note/detail?id={note_id}")
req.add_header("Authorization", os.environ["GETNOTE_API_KEY"])
req.add_header("X-Client-ID", os.environ["GETNOTE_CLIENT_ID"])
resp = urllib.request.urlopen(req)
print(resp.read().decode())
''')
```

Step 2: `terminal` 执行
```bash
python3 /tmp/getnote_detail.py
```

## 轮询伪代码

```
1. save → task_id
2. sleep 15s → POST progress → status
3. processing → 继续等（短内容 60s 后 detail 有内容）
4. GET detail → content + web_page.content
5. 忽略 error_msg，取实际内容
```
