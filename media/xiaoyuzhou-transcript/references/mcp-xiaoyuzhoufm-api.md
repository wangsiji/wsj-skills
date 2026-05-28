# mcp-xiaoyuzhoufm 包 API 参考

Node.js 包，封装了小宇宙 FM 的公开接口。

## 安装

```bash
npm install mcp-xiaoyuzhoufm
```

## 导出模块

```javascript
const { XiaoyuzhoufmClient } = require('mcp-xiaoyuzhoufm');
```

- `XiaoyuzhoufmClient` — 客户端类（注意：不是 `XiaoyuzhouFM`）
- 其他导出：`config`, `getConfig`, `mcpServer`, `MCPServer`, `HttpServer`, `StdioHandler`, `downloadXiaoyuzhouAudio`

## 客户端方法

### `extractEpisodeId(url)` → Promise<string>
从播客 URL 提取 24 位 hex episode ID。

```javascript
const id = await xiaoyu.extractEpisodeId('https://www.xiaoyuzhoufm.com/episode/6a06c33ae1eb34a93973c9c1');
// → '6a06c33ae1eb34a93973c9c1'
```

### `getEpisodeInfo(episodeId)` → Promise<object>
获取单集完整信息。

**返回结构：**
```javascript
{
  success: true,
  episode: {
    id: '6a06c33ae1eb34a93973c9c1',
    url: 'https://www.xiaoyuzhoufm.com/episode/...',
    title: 'Vol 54-如何不费力的坚持一件事？',
    // 以下字段仅在有数据时存在：
    transcript: [          // 文字稿数组（如果有）
      { start: 0, end: 7.2, content: '（片头音乐）' },
      { start: 7.2, end: 15.8, content: '主播：...' }
    ],
    transcriptMediaId: '...',   // 音频文件标识（非文字）
    shownotes: 'HTML string'    // Show Notes HTML
  }
}
```

### `getEpisodeMetadata(episodeId)` → Promise<object>
获取单集元数据（未验证具体字段）。

### `downloadAudio(episodeId, options?)` → Promise
下载单集音频文件。

## 已知问题

- 并非所有节目都有 `transcript` 字段。仅创作者上传或平台自动生成了文字稿的节目才有。
- 没有 `transcript` 字段的节目，通常 `episode` 只返回 `{id, url, title}` 三个字段。
- 初始化时会在控制台输出 info 日志，不影响功能。
- 继承自 MCP server 框架，初始化时自动注册工具。
