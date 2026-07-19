# 排错表

## 文件定位

| 症状 | 处理 |
|------|------|
| 文件存到了 Clipping/ 而非 Raw/ | `mv` 搬到 `Raw/`，不要 `cp`（避免残留两份） |
| 找不到文件 | `find ~/projects/wsj-second-brain -name "*.md" -mmin -3` |

## getnote

| 症状 | 处理 |
|------|------|
| `error_msg="生成笔记失败"` | 以 status 为准，调 detail 拿 content。内容通常在 |
| `status=processing` 超过 3min | 早停条件仅适用于网页/X 链接。媒体剪藏继续等 |
| detail 返回 401 未授权 | 检查 Authorization header 格式 — 裸 key，**无 Bearer** |
| content="" 但 web_page.content 非空 | 转写稿已就绪，AI 总结还需等待 |

## 扩展/VNC

| 症状 | 处理 |
|------|------|
| X.com 空白/只看到登录页 | Cookie 过期 → 更新 `~/.config/xfetch/session.json` |
| Extension SW not found! | 等 5-10s 重试 |

## 内容清理

| 症状 | 处理 |
|------|------|
| 合并后 H1 重复 | 合并前去 body 中的所有 `<h1>` / `# 标题` |
| 剪藏原文含 `<video>` + `blob:` | `re.sub(r'<video .*?</video>', '', body, flags=re.DOTALL)` |
| 公众号 format=markdown 只有 CSS | 这是图片文章（item_show_type: 8），用 format=json 取图片 |

## 环境

| 症状 | 处理 |
|------|------|
| 磁盘不足 | `pip3 cache purge && npm cache clean --force && sudo journalctl --vacuum-time=7d` |
| Xvfb/Chrome 未就绪 | `bash scripts/vnc-startup.sh` |
| 公众号 sync 返回"已是最新"但无新文件 | API Key 可能过期，直调 API 确认 |
