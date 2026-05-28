# X/Twitter Article & 推文剪藏

X/Twitter 内容需要登录态 + JavaScript 渲染，不能直接用方案B 的 `clip.py`。

## 工作流

### 1. 检查认证 & 获取 Cookie

```bash
xreach auth check
# 输出: ✓ Authenticated
# 获取完整 cookie 值（用于浏览器注入）:
cat ~/.config/xfetch/session.json
# → {"authToken": "...", "ct0": "..."}
```

### 2. 浏览器注入 Cookie 提取内容

用 Hermes 的浏览器工具（非 VNC 桌面）：

```
# 第一步: 导航到 x.com 建立同源上下文
browser_navigate('https://x.com')

# 第二步: 注入 cookie（必须在 x.com 域下）
browser_console(expression="document.cookie = 'auth_token=VALUE; path=/; domain=.x.com; secure;'")
browser_console(expression="document.cookie = 'ct0=VALUE; path=/; domain=.x.com; secure;'")

# 第三步: 导航到推文/文章
browser_navigate('https://x.com/user/status/{tweet_id}')
# 或（X Article 长文）
browser_navigate('https://x.com/i/article/{article_id}')

# 第四步: 提取完整内容（使用 TreeWalker 避免重复文本）
browser_console(expression="const root = document.querySelector('main') || document.body; const walker = document.createTreeWalker(root, 4); const parts = []; let node; while (node = walker.nextNode()) { const text = node.textContent.trim(); if (text && text.length > 2) { const tag = node.parentElement?.tagName?.toLowerCase(); if (tag === 'script' || tag === 'style') continue; parts.push(text); } }; parts.join('\\n');")
```

### 3. X Article 识别

- 推文文本只有 `https://t.co/...` 说明是 X Article
- 解析 t.co 找到真实 article_id: `curl -sIL "https://t.co/..." | grep -i "^location:"`
- 真实 URL: `https://x.com/i/article/{article_id}`
- 注: xreach CLI 的 tweet API 只返回 t.co 链接，不返回文章内容

### 4. 方案A 可视化操作

用 noVNC 桌面打开 Chrome，走 Web Clipper 扩展（快捷键 Ctrl+Shift+O）：
- 先在 VNC 桌面的 Chrome 里导航到 x.com 并注入 cookie
- 打开目标文章
- 按 Ctrl+Shift+O 触发弹窗 → Tab 到保存按钮 → Enter

## 已知限制

- Hermes 的 browser tool 和 VNC 桌面的 Chrome 是两个独立会话（cookie 不互通）
- xreach CLI 不支持读 X Article 内容（只返回 t.co 链接）
- 没有已知的 API 能直接获取 X Article 全文
- 浏览器注入 cookie 必须在 `https://x.com` 域下，不能在登录页（跨域安全限制）
