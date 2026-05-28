---
name: xiaoyuzhou-transcript
description: 从小宇宙播客页面提取文字稿（带时间戳或纯文本）。利用页面内置的 __NEXT_DATA__ JSON 数据直接读取 transcript，无需 ASR 语音转写。仅适用于创作者上传或平台生成了文字稿的节目。
---

# 小宇宙播客文字稿提取

从小宇宙播客单集 URL 中提取文字稿，利用小宇宙页面已公开的文字稿缓存，无需语音识别。

## 三种提取方式

### 方式一：npm 包 `mcp-xiaoyuzhoufm`（推荐，最稳定）

通过第三方 Node.js 包直接调用小宇宙公开 API，支持提取单集信息（含文字稿）、下载音频。

**安装：**
```bash
npm install mcp-xiaoyuzhoufm
```

**提取脚本（`get_transcript.js`）：**
```javascript
const { XiaoyuzhoufmClient } = require('mcp-xiaoyuzhoufm');

async function getTranscript() {
  const xiaoyu = new XiaoyuzhoufmClient();
  const episodeUrl = 'https://www.xiaoyuzhoufm.com/episode/{EID}';
  
  const episodeId = await xiaoyu.extractEpisodeId(episodeUrl);
  const episodeInfo = await xiaoyu.getEpisodeInfo(episodeId);
  
  if (!episodeInfo.success || !episodeInfo.episode.transcript) {
    console.log('该节目未生成文字稿');
    return;
  }
  
  episodeInfo.episode.transcript.forEach(item => {
    const m = Math.floor(item.start / 60);
    const s = Math.floor(item.start % 60);
    console.log(`[${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}] ${item.content}`);
  });
}
getTranscript();
```

**注意：** `getEpisodeInfo` 返回结构为 `{success, episode}`。`episode` 包含 `id, url, title, transcript, transcriptMediaId, shownotes` 等字段。如果 `transcript` 字段不存在则该期无文字稿。

完整脚本模板见 `templates/get_transcript.js`。

### 方式二：API 接口直取

通过小宇宙公开 API 直接获取 JSON 格式文字稿，无需加载页面。

### 方式三：页面 __NEXT_DATA__ 提取（备选）

// ... existing NEXT_DATA method content ...

```
GET https://www.xiaoyuzhoufm.com/api/v1/episodes/{EPISODE_ID}/transcript
```

返回 JSON 数组，格式：
```json
[
  {"start": 0, "end": 7.2, "content": "（片头音乐）"},
  {"start": 7.2, "end": 15.8, "content": "主播：各位听众朋友们大家好..."}
]
```

Shell 命令：
```bash
EPISODE_ID=$(echo "$URL" | grep -oP '[a-f0-9]{24}')
curl -sS \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Referer: https://www.xiaoyuzhoufm.com/episode/${EPISODE_ID}" \
  -H "Accept: application/json" \
  "https://www.xiaoyuzhoufm.com/api/v1/episodes/${EPISODE_ID}/transcript"
```

需浏览器 User-Agent 和 Referer 头。如被反爬拦截，切换方式二。

### 方式三：页面 __NEXT_DATA__ 提取（备选）

小宇宙网页端（Next.js 应用）在 `__NEXT_DATA__` 中嵌入了完整的节目数据，其中 `episode.transcript` 字段包含文字稿内容。直接解析该 JSON 即可提取。

## 提取步骤

### 1. 打开播客页面

```
browser_navigate('https://www.xiaoyuzhoufm.com/episode/{eid}')
```

### 2. 提取 transcript 数据

使用 `browser_console` 工具执行：

```javascript
// 检查是否有文字稿
JSON.parse(document.getElementById('__NEXT_DATA__').textContent).props.pageProps.episode.transcript
```

### 3. 判断文字稿类型

- **有完整文字稿（最佳）**：`transcript` 字段是包含 `paragraphs` 或其他文本结构的对象，可直接提取带时间戳的文字
- **仅有 mediaId（无文字稿）**：`transcript` 字段只有 `{mediaId: "..."}`，说明这期没有内置文字稿，只能提取 Show Notes 的时间戳标注
- **有 transcriptMediaId 但无文本**：同上，只有媒体文件关联，无文字内容

### 4. 提取 Show Notes 作为备选

如果无完整文字稿，Show Notes 中可能包含带时间戳的高亮标注：

```javascript
JSON.parse(document.getElementById('__NEXT_DATA__').textContent).props.pageProps.episode.shownotes
```

返回的 HTML 中包含 `<span class="timestamp" data-timestamp="秒数">MM:SS</span>` 格式的时间戳标注。

## 已知限制

- **不是所有节目都有文字稿**：仅创作者主动上传字幕或平台支持自动生成的节目才有
- **文字稿格式不统一**：部分节目的 `transcript` 是纯字符串，部分是结构化对象（带段落/时间戳）
- **页面需要正常加载**：被反爬拦截时（无 residential proxy）可能无法获取数据，可尝试 curl 直取 HTML 后解析 `__NEXT_DATA__`
- **时间戳格式**：Show Notes 的时间戳 `data-timestamp` 单位是秒，需自行转换为 MM:SS

## 输出格式建议

```markdown
## 文字稿

### 时间戳版本
```
[00:00:00] 内容开始...
[00:01:04] 正文段落...
...
```

### 纯文本版本
如需无时间戳版本，直接拼接文字稿文本即可。
```

## 相关资源

- 小宇宙播客 URL 格式：`https://www.xiaoyuzhoufm.com/episode/{24位hex}`
- 音频文件提取：`transcriptMediaId` 字段包含音频文件名，可通过小宇宙 API 获取音频流
