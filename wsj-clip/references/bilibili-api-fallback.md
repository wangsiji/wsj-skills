# B站 API 备用方案

当 B站页面（浏览器/curl/defuddle）被反爬拦截时，使用官方 API 直接获取视频元数据。

## API

```
GET https://api.bilibili.com/x/web-interface/view?bvid={BVID}
```

无需认证，仅需 `Referer: https://www.bilibili.com/` 头。

BVID 格式：`BV1i1ehzQEoc`（视频 URL 中 `/video/` 后的部分）

## Python 提取

```python
import json, urllib.request

bvid = "BV1i1ehzQEoc"
req = urllib.request.Request(
    f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
    headers={"Referer": "https://www.bilibili.com/", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
)
data = json.loads(urllib.request.urlopen(req).read())

if data['code'] == 0:
    v = data['data']
    title = v['title']
    author = v['owner']['name']
    desc = v['desc']
    duration = v['duration']  # seconds
    stats = v['stat']
else:
    # API 返回错误（如 BVID 不存在）
    pass
```

## 返回字段说明

| 字段 | 路径 | 说明 |
|------|------|------|
| title | `data.title` | 视频标题 |
| author | `data.owner.name` | UP主名称 |
| desc | `data.desc` | 视频简介 |
| duration | `data.duration` | 时长（秒） |
| view | `data.stat.view` | 播放量 |
| danmaku | `data.stat.danmaku` | 弹幕数 |
| like | `data.stat.like` | 点赞数 |
| coin | `data.stat.coin` | 投币数 |
| favorite | `data.stat.favorite` | 收藏数 |
| share | `data.stat.share` | 分享数 |
| pic | `data.pic` | 封面图 URL |

## 触发条件

- B站页面返回"出错啦"（curl/defuddle 拦截）
- 浏览器打开 B站超时（CAPTCHA/反爬）
- 目标只是获取视频基本信息（无需完整字幕/文案）

## 限制

- 只返回视频基本信息（标题/简介/UP主/统计），**不返回完整文案/字幕**
- 如需完整文案，走 clip 技能的 **Method B: getnote 媒体剪藏**（B站视频自动转写）
- API 字段 `data.t`（标签）通常为空数组

## ⚠️ JSON 解析陷阱

B站 API 返回的 `desc`（简介）字段可能包含**未转义的控制字符**（0x00-0x1F 范围内的原始字符），导致 Python 的 `json.loads()` 默认严格模式抛出 `JSONDecodeError: Invalid control character`。

### 症状

```
json.decoder.JSONDecodeError: Invalid control character at: line 1 column 20001
```

### 解法（三选一）

**解法 A：通过 shell 用 python3 -c 单行提取（最稳定）**
```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=$BVID" \
  -H "Referer: https://www.bilibili.com/" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
v=d['data']
print(f\"TITLE: {v['title']}\")
print(f\"UP: {v['owner']['name']}\")
print(f\"DUR: {v['duration']}\")
print(f\"VIEWS: {v['stat']['view']}\")
"
```

**解法 B：json.loads 使用 strict=False**
```python
import json
d = json.loads(raw_json_str, strict=False)  # 允许控制字符
```

**解法 C：decode + errors='replace' 预处理**
```python
raw = response.read().decode('utf-8', errors='replace')
d = json.loads(raw)
```

### 推荐做法

如果只需要几个字段（标题/UP主/时长/统计），用 **解法 A**——`python3 -c` 单行提取最简洁，控制字符不会影响管道传输。如果需要在 `execute_code` 沙箱中完整解析，用 **解法 B**——`strict=False` 比 `errors='replace'` 更轻量，且不会丢失 desc 字段内容。

## 与 getnote 的配合

```
B站 API 获取基本信息（标题/作者/时长/简介）
  ↕ 并行
getnote 处理视频字幕/文案（异步轮询）

合并输出：
  # 视频标题
  
  ## AI 智能总结  ← getnote 内容
  ## 视频信息     ← API 元数据
  UP主、时长、播放量、简介
  ## 完整文字稿   ← getnote 内容
```

## 长视频 AI 总结等待策略（重要）

与长播客同理，B站的长视频（60min+）也需要额外等待时间。

**典型时间线：**
- 提交后 1~3min：`web_page.content` 已有字幕/转写稿
- 提交后 5~8min：`data.note.content` 才出现 AI 总结

**不要犯的错：**
首轮轮询看到 `status=processing` + `content=""` + `error_msg="生成笔记失败"` 就宣布"AI 总结不可用" → **会被用户纠正**。转写稿已有≠总结已出。

**正确做法：**
1. 拿到 `note_id` 后先取 `web_page.content`（转写稿通常已有）
2. 如果 `content=""`，设 cron 任务 5 分钟后复查
3. cron 里调 `/note/detail?id={note_id}`，有内容则更新原文件

详见小宇宙参考中的同款流程：`references/xiaoyuzhou-podcast-clipping.md` → 步骤 4.5
