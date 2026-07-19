# X Article → Obsidian Vault 剪藏流程

## 场景
X 推文只包含 t.co 链接（X Article 长文），需要绕过登录墙读取全文并保存到 vault。

## 前置条件
- xreach 已认证（`xreach auth check` → `✓ Authenticated`）
- xfetch session 文件存在：`~/.config/xfetch/session.json`

## 完整流程

### Step 1: 解析 t.co 链接

```bash
# 从推文文本中拿到 t.co URL
curl -sIL "https://t.co/XXXXXX" | grep -i "^location:" | tail -1
# → location: https://x.com/i/article/{article_id}
```

### Step 2: 读取 session token

```bash
cat ~/.config/xfetch/session.json
# → {"authToken": "...", "ct0": "..."}
```

### Step 3: 浏览器注入 cookie 获取全文

```python
# 1. Navigate to x.com（建立 cookie domain）
# 2. Inject cookies:
#    document.cookie = "auth_token=VALUE; path=/; domain=.x.com; secure; samesite=lax;"
#    document.cookie = "ct0=VALUE; path=/; domain=.x.com; secure; samesite=lax;"
# 3. Navigate to the article URL
# 4. Extract content:
#    document.querySelector('main').innerText
```

注意：`auth_token` 是 HttpOnly，JS 无法用 `document.cookie` 读取到，但浏览器会正常发送。

### Step 4: 保存到 vault

格式化为 Obsidian Markdown（frontmatter + body），保存到：

```bash
# X 文章剪藏统一放这里
/home/wangsiji/projects/wsj-second-brain/00-LLM-WiKi/Raw/{title-slug}.md
```

### Step 5: 验证

```bash
ls -la /home/wangsiji/projects/wsj-second-brain/00-LLM-WiKi/Raw/ | tail -5
```

### 持久化 cookie（适用于 VNC Chrome 重启后仍登录）

用 Playwright 将 cookie 写入 Chrome 持久化配置：

```python
from playwright.async_api import async_playwright
import asyncio

async def inject_x_cookies(profile_dir, auth_token, ct0):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage'],
        )
        await browser.add_cookies([
            {'name': 'auth_token', 'value': auth_token,
             'domain': '.x.com', 'path': '/', 'secure': True, 'httpOnly': True, 'sameSite': 'Lax'},
            {'name': 'ct0', 'value': ct0,
             'domain': '.x.com', 'path': '/', 'secure': True, 'httpOnly': False, 'sameSite': 'Lax'},
        ])
        page = await browser.new_page()
        await page.goto('https://x.com/', wait_until='domcontentloaded')
        await asyncio.sleep(3)
        await browser.close()

asyncio.run(inject_x_cookies('/home/wangsiji/.config/google-chrome', auth_token, ct0))
```

Playwright 调用 `add_cookies()` 通过 CDP 的 `Storage.setCookies` 写入 Chrome profile 的 SQLite cookie 存储，重启后仍有效。

⚠️ 需要在有 DISPLAY 的环境中运行（Playwright headless=false 需要 X server）。

## 坑：Chrome CDP 远程调试端口绑定失败

当 Chrome 使用默认 profile（`~/.config/google-chrome`）启动时，`--remote-debugging-port=9222` 经常无法绑定——SingletonLock/SingletonSocket 阻止了 CDP 监听。

**现象**：Chrome 正常启动，但 CDP port 未监听，`curl http://localhost:9222/json/version` 无响应。

**解决方案**：
1. 用 `--user-data-dir=/tmp/chrome-profile` 启动独立 profile（但会丢失 X cookie 和下载目录设置）
2. 或者删除 lock 文件后再启动：
   ```bash
   rm -f ~/.config/google-chrome/SingletonLock ~/.config/google-chrome/SingletonSocket
   ```
3. 或者不用 CDP，直接用 Hermes 浏览器（`browser_navigate` + `browser_console`）做 cookie 注入提取，更可靠

**推荐**：CDP 绑定不可靠，优先用 Hermes 浏览器 cookie 注入剪藏。VNC Chrome 留给用户手动操作。

## 已知工作会话

| 日期 | 内容 | 状态 |
|------|------|------|
| 2026-05-27 | @blackanger (AlexZ) 的 "X 观察 #1：AI 编程的下一阶段" | ✅ 已剪藏 |
| 2026-05-27 | @ai_xiaomu 的 "X涨粉模板，照着做轻松破万" 文章 | ✅ 已剪藏 |
| 2026-05-26 | @ChrisWangwy 的 X Article | ✅ 已剪藏 |
| 2026-05-22 | TTkitty_ Obsidian 教程 | ✅ 已剪藏 |
