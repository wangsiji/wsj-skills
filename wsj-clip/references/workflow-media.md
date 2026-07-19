# 媒体剪藏详细流程（Method B）

| 来源 | 方法 | 备注 |
|------|------|------|
| B站（bilibili.com） | getnote API 取字幕文案 | B站 API 备用（详见 references/bilibili-api-fallback.md） |
| 小宇宙（xiaoyuzhoufm.com） | getnote API 取转写稿 + 浏览器取 show notes | 详见 references/xiaoyuzhou-podcast-clipping.md |

## 流程

1. 提交 getnote（save → 取 task_id）
2. 轮询进度（progress → 取 note_id）
3. 取详情（detail → content + web_page.content）
4. 长内容（60min+）：首轮 content="" 正常，设 cron 5min 复查
5. 合并输出（scripts/merge-clip.py）

> getnote 通用规则详见 `references/getnote-api.md`。
