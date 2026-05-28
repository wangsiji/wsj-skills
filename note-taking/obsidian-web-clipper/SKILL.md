---
name: obsidian-web-clipper
description: Clip web pages to the Obsidian vault on a headless VPS (no Obsidian GUI).
triggers:
  - "clip this page to obsidian"
  - "剪藏到 obsidian"
  - "save this article to vault"
  - "web clipper 配置"
  - "obsidian web clipper"
  - "cdo clip"
  - "vnc clip"
  - "vnc 剪藏"
  - "search and clip"
  - "推特搜索剪藏"
  - "搜索...然后剪藏"
---

# Obsidian Web Clipper (VPS Edition)

Five approaches for clipping web content to the Obsidian vault at `~/projects/wsj-second-brain/`:

- **方案A**: noVNC 桌面 + Chrome 扩展（交互式，手动操作）
- **方案B**: CLI 脚本（自动化，headless）
- **方案C**: Save file 模式（无 Obsidian 时的备用方案）
- **方案D**: xreach API 直接格式化推文（快速替代，仅用于无需扩展剪藏的快速任务）
- **方案E**: VNC CDP + 扩展 Service Worker 自动化（推荐方案，见下方 Pitfalls→CDP 章节）

## 方案选择优先级（重要）

当用户要求「剪藏」时，按以下优先级执行：

1. **方案E（VNC CDP + 扩展）** — 标准剪藏流程，通过 `vnc-clip.py` 调用 Obsidian Web Clipper 扩展。最符合「剪藏」语义。
2. **方案D（xreach API）** — 仅用于：用户明确说「用 xreach 剪」、或只是快速归档推文文本无需扩展处理。
3. **方案A/B/C** — 各自场景下使用。

⚠️ **不要用方案D（xreach API 手动格式化）替代方案E**。当用户说「剪藏」时，预期的是扩展的完整剪藏流程。xreach API 只能用于搜索发现内容 + 获取推文信息，真正的剪藏操作必须走扩展/脚本。

---

## 方案A：noVNC 桌面 + Chrome 扩展（手动操作，用户偏好）

用户明确首选 VNC 剪藏方法。当用户点名要用 VNC 时，不要自动改用 Hermes 浏览器方案。

### 启动桌面

```bash
# 1. Xvfb 虚拟显示器
Xvfb :2 -screen 0 1920x1080x24 &

# 2. openbox 窗口管理器（让 xdotool windowactivate 可用）
openbox --replace &

# 3. x11vnc（密码 ~/.vnc/passwd）
x11vnc -display :2 -localhost -forever -shared -rfbauth ~/.vnc/passwd -noshm &

# 4. websockify+noVNC
websockify --web=/home/wangsiji/noVNC 6080 localhost:5900 &
```

### 启动 Chrome 并加载 Web Clipper 扩展

**使用默认 profile（保留 X 登录 cookie 和下载设置）：**

```bash
DISPLAY=:2 google-chrome-stable --no-sandbox --disable-dev-shm-usage \
  --start-maximized \
  --load-extension=/tmp/obsidian-clipper/dist
```

**不要**使用 `--user-data-dir=/tmp/...` 临时 profile，会丢失：
- X 登录 cookie（需重新注入）
- Chrome 下载目录设置（下载到了错误位置）

### 访问

`http://192.3.16.123:6080/vnc.html`

VNC 密码：test1234（设置在 `~/.vnc/passwd`）

### vault 端插件

- **obsidian-local-rest-api** 社区插件已安装在 vault 中（插件目录存在，但可能未在 `community-plugins.json` 中启用）
- 启用方式：编辑 `$VAULT/.obsidian/community-plugins.json`，在数组中添加 `"obsidian-local-rest-api"`
- 插件源：`https://github.com/coddingtonbear/obsidian-local-rest-api`
- 版本：4.1.0
- 插件配置：`$VAULT/.obsidian/plugins/obsidian-local-rest-api/data.json`
  - 端口：27123
  - API Key：`obsidian-local-rest-api-key-2026`
  - allowedOrigins：`chrome-extension://*` 和 `http://localhost*`

### REST API 的限制

**REST API 需要 Obsidian GUI 运行才能生效。** `main.js` 是 Obsidian 插件，依赖 Obsidian API，无法直接通过 `node` 启动。

在 headless VPS 上，如果 Obsidian 未安装或未运行：
- Web Clipper 扩展的 "Add to Obsidian" 模式无法工作
- 有效替代方案：使用 **"Save file"** 模式（见下文）
- 或者使用 方案B 的 CLI 脚本
- **重要限制**：该插件是 Obsidian 插件，`main.js` 依赖 Obsidian API（`obsidian.ts`），无法通过 `node main.js` 独立运行。如果 Obsidian 未在运行（VPS 无 GUI），REST API 不可用，Web Clipper 扩展的"发送到 vault"功能不可用。替代方案见 方案B CLI 脚本。

### 构建 Web Clipper 扩展（如需重新构建）

```bash
git clone --depth=1 https://github.com/obsidianmd/obsidian-clipper.git /tmp/obsidian-clipper
cd /tmp/obsidian-clipper
npm install
npm run build:chrome       # 浏览器扩展 → dist/
npm run build:cli           # CLI 模式 → dist/cli.cjs
```

---

## 方案B：CLI 脚本自动化剪藏

### 脚本位置

`~/projects/wsj-second-brain/clip.py`

### 原理

Chrome headless `--dump-dom` 获取渲染后的完整 DOM → bs4 智能定位文章主体 → markdownify 转 markdown → 写入 vault（含 frontmatter）

### 用法

```bash
cd ~/projects/wsj-second-brain

# 保存到默认目录 (Clippings/)
python3 clip.py <url>

# 保存到 _wiki/raw/articles/（llm-wiki 原始资料层）
python3 clip.py <url> --dir "_wiki/raw/articles"

# 只输出到终端
python3 clip.py <url> --stdout

# 自定义输出路径
python3 clip.py <url> -o ~/path/to/note.md
```

### 输出格式

每篇笔记自动生成 frontmatter：

```yaml
---
title: 页面标题
source: https://example.com/article
domain: example.com
clipped: 2026-05-26
author: 作者名 (如有)
description: 描述 (如有)
---
```

### 依赖

- Python 3 + bs4 + markdownify（已安装）
- Chrome/Chromium（已安装）

---

## 方案C：Save file 模式（无 Obsidian 时的备用方案）

当 Obsidian GUI 未运行、REST API 不可用时，Web Clipper 扩展的 **Save file** 模式可以直接下载 `.md` 文件。

### 设置方法

通过 VNC Chrome 手动设置（仅需一次）：

1. 打开 VNC：`http://<VPS_IP>:6080/vnc.html`（密码 见 `~/.vnc/passwd`）
2. Chrome 已预加载扩展 `--load-extension=/tmp/obsidian-clipper/dist`
3. 点击扩展图标 → 右下角 ⚙️ 进入设置
4. **General → Save behavior** → 从 `Add to Obsidian` 改为 **`Save file`**
5. 保存设置后关闭

设置选项（来自 `settings.html`）：
```html
<option value="addToObsidian">Add to Obsidian</option>   <!-- 需要 REST API -->
<option value="copyToClipboard">Copy to clipboard</option>
<option value="saveFile">Save file</option>               <!-- 无 Obsidian 时可用 -->
```

### 使用

1. 在目标页面上点击 Web Clipper 扩展图标
2. 点击 **Save file** 按钮 → Chrome 下载 `.md` 文件
3. 文件默认保存到 Chrome 下载目录

### Chrome 下载目录配置（Preferences JSON）

可直接修改 Chrome 配置文件设置下载目录，无需手动操作：

```bash
python3 -c "
import json
with open('/home/wangsiji/.config/google-chrome/Default/Preferences') as f:
    prefs = json.load(f)
if 'download' not in prefs:
    prefs['download'] = {}
prefs['download']['default_directory'] = '/home/wangsiji/projects/wsj-second-brain/Inbox/LLM-WiKi/Raw/Clippings'
with open('/home/wangsiji/.config/google-chrome/Default/Preferences', 'w') as f:
    json.dump(prefs, f)
"
```

修改后需重启 Chrome 生效。

### 推荐目标路径

```
/home/wangsiji/projects/wsj-second-brain/Inbox/LLM-WiKi/Raw/Clippings/
```

---

## 方案D：xreach API 直接格式化推文（快速替代，谨慎使用）

⚠️ **警告**：此方案通过 xreach API 获取推文文本后手动格式化 Markdown 写入 vault，**不经过 Obsidian Web Clipper 扩展**。扩展的剪藏包含 defuddle 内容提取、模板处理、图片下载等功能，手动格式化会丢失这些处理。仅用于快速归档、无需扩展处理的场景。

X/Twitter 推文（非 X Article 长文）的快速保存方式：通过 **xreach** API 获取推文全文和结构化数据，直接格式化为 Obsidian Markdown 写入 vault。无需浏览器、VNC 或 Chrome。

**适用场景**：
- 搜索 Twitter 上高互动推文并批量剪藏
- 单条推文剪藏（比浏览器方案快 10 倍）
- 需要保留互动数据（点赞/转发/收藏数）

### 前置条件

```bash
# 确认 xreach 已安装且认证通过
xreach auth check
# ✓ Authenticated

# xreach 位置（npm global）
which xreach
# ~/.npm-global/bin/xreach

# 凭据文件
ls ~/.config/xfetch/session.json
```

### 核心流程

```bash
# 1. 搜索推文（返回 JSON，含 user, likeCount, retweetCount, bookmarkCount 等）
xreach search "obsidian web clipper" -n 20

# 2. 获取单条推文详情（含完整文本）
xreach tweet POST_ID

# 3. 获取推文原始 JSON
xreach tweet POST_ID --json

# 4. 格式化处理：提取推送文本 + 用户信息 + 互动数据 → frontmatter + markdown
```

### Python 格式化和保存示例

```python
import json, subprocess
from datetime import date

# 获取推文
r = subprocess.run(["xreach", "tweet", tweet_id, "--json"],
    capture_output=True, text=True, timeout=15)
tweet = json.loads(r.stdout)

# 构建 frontmatter
today = date.today().isoformat()
text = tweet.get("text", "")
user = tweet.get("user", {})
sn = user.get("screenName", "?")
name = user.get("name", "?")

fm = f"""---
title: {text[:60].strip()!r}
source: https://x.com/{sn}/status/{tweet_id}
domain: x.com
clipped: {today}
author: "@{sn} ({name})"
created: {tweet.get("createdAt", "unknown")}
engagement:
  likes: {tweet.get("likeCount", 0)}
  retweets: {tweet.get("retweetCount", 0)}
  bookmarks: {tweet.get("bookmarkCount", 0)}
  replies: {tweet.get("replyCount", 0)}
---

{text}
"""

filename = re.sub(r'[\\/:*?"<>|]', '_', text[:60])
filename = re.sub(r'\s+', '_', filename.strip())
path = f"{output_dir}/{filename}.md"
with open(path, "w") as f:
    f.write(note)
```

### 保存目录

推文默认保存到 `~/projects/wsj-second-brain/Clippings/`。

### 优先使用 API 而非浏览器的判断规则

| 内容类型 | 方法 | 原因 |
|---|---|---|
| 普通推文（tweet） | xreach API | 快，有结构化数据 |
| X Article 长文 | 浏览器 cookie 注入 | API 不返回全文 |
| 引用的外部链接 | 浏览器 headless 或 VNC | 非 X 内容 |

### ⚠️ 注意：xurl 未安装

系统上 **xurl CLI 未安装**。Twitter/X 相关操作统一用 **xreach**（已安装于 `~/.npm-global/bin/xreach`）。xurl skill 中的命令仅供参考，实际执行前需将 `xurl search` / `xurl tweet` 替换为 `xreach search` / `xreach tweet`。

---

## Pitfalls

### 方案B 脚本提取受登录限制的内容

方案B 的 `clip.py` 使用 Chrome headless `--dump-dom`，对需要登录才能查看的页面（X Articles、付费文章等）会只看到登录页面。

**X/Twitter 内容剪藏分两种情况**：

| 内容类型 | 方法 | 说明 |
|---|---|---|
| 普通推文 | **方案D：xreach API** | xreach tweet --json → 格式化 → 写入 vault。最快，无需浏览器 |
| X Article 长文 | **浏览器 cookie 注入** | Hermes browser_navigate → browser_console 注入 auth_token + ct0 → DOM 提取全文 |

**普通推文**（~95% 的 Twitter 内容）：用 `xreach tweet ID --json` 获取完整文本和结构化数据，然后格式化保存。见 方案D / `references/xreach-tweet-clipping.md`。

**X Article 长文**（`x.com/i/article/{id}` 格式）：推文只包含 t.co 链接，需要浏览器 cookie 注入读取全文。详见 `references/x-article-clipping.md`。核心流程：
1. `xreach auth check` 确认已登录
2. 读取 `~/.config/xfetch/session.json` 获取 auth_token 和 ct0
3. `browser_navigate` 到 x.com 建立同源 cookie 域
4. `browser_console` 注入两个 cookie
5. 导航到文章 URL，`document.querySelector('main').innerText` 提取全文
6. 格式化为 markdown 写入 vault（直接 `write_file` 而非通过 clip.py）

**VNC Chrome 持久化 X 登录**：要在 VNC Chrome 中持久登录 X，使用 Playwright 将 cookies 写入 Chrome profile：
```python
async with async_playwright() as p:
    ctx = await p.chromium.launch_persistent_context(
        user_data_dir='/home/wangsiji/.config/google-chrome',
        headless=False,
        args=['--no-sandbox', '--disable-dev-shm-usage'],
    )
    await ctx.add_cookies([...])  # auth_token + ct0
```
需要设置 `DISPLAY=:2` 环境变量（对应 Xvfb display 编号），否则 Playwright 的 headed 模式会报 "Missing X server or $DISPLAY"。

### ⚠️ 不要用方案D（xreach API 手动格式化）替代方案E（vnc-clip.py CDP 扩展）剪藏

这是一个**已验证的纠正信号**：当用户要求「剪藏」时，必须走 Obsidian Web Clipper 扩展的完整流程（方案E: vnc-clip.py），不能只用 xreach API 抓取文本后手动写 .md 文件。

**原因**：
- 用户预期的「剪藏」是通过扩展执行的（等价于手动点扩展按钮）
- 方案D 跳过了扩展的 defuddle 内容提取、模板处理、图片保存等流程
- 方案D 保存到 `Clippings/` 目录，方案E 保存到 `Inbox/LLM-WiKi/Raw/Clippings/`，目录不一致

**正确流程**：用 xreach 搜索发现 → 用 vnc-clip.py 剪藏 → 清理旧的手动文件。

### defuddle + linkedom 提取失败

官方的 `obsidian-clipper` CLI（`dist/cli.cjs`）使用 linkedom 作为 DOM 解析器，与 defuddle 内容提取库配合时效果很差——标题和正文都为空。根源是 linkedom 实现不完整，defuddle 依赖的 DOM API 缺失。

**修复方法**：在 build 脚本中添加 `navigator` polyfill 可以消除报错，但 defuddle 提取本身仍然不可靠。推荐直接用 方案B 脚本。

### VNC 桌面分辨率

Xvfb 默认 1920x1080x24 即可。如果 Chrome 窗口太小影响操作，可放大 `--window-size` 参数。

### Obsidian Web Clipper 源码构建

```bash
cd /tmp/obsidian-clipper
# 构建 Chrome 扩展（耗时约 2 分钟）
npx webpack --env BROWSER=chrome --mode production
# 构建 CLI（几秒钟）
npm run build:cli
```

CLI 的 `navigator` polyfill 修复：在 `scripts/build-cli.mjs` 的 polyfill banner 中添加：

```js
if (!globalThis.navigator) globalThis.navigator = { userAgent: "cli", platform: "linux", userAgentData: null };
if (!globalThis.window.navigator) globalThis.window.navigator = globalThis.navigator;
```

### 键盘快捷键（扩展定义，Xvfb 下不可用）

Obsidian Web Clipper 1.6.1 预定义以下快捷键（manifest 中的 `commands`）：

| 快捷键 | 功能 | 说明 |
|---|---|---|
| `Alt+Shift+O` | Quick Clip | 打开弹窗 → 500ms 后自动发 `triggerQuickClip` 消息 |
| `Ctrl+Shift+O` | Open Clipper | 普通剪藏弹窗（与 Chrome 书签快捷键冲突） |
| `Alt+Shift+H` | Toggle Highlighter | 高亮模式 |
| `Alt+Shift+R` | Toggle Reader | 阅读模式 |

**Xvfb 下键盘快捷键无效**：即使安装了 openbox 窗口管理器，xdotool 发送的 `alt+shift+o` 等组合键也无法触发 Chrome 扩展。根源是 Xvfb 的输入事件无法正确路由到 Chrome 的扩展快捷键处理器。不在此方向上投入时间。

### openbox 窗口管理器

Xvfb 默认无窗口管理器，`xdotool windowactivate` 会报错。安装 openbox 可修复窗口激活链：

```bash
sudo apt-get install -y openbox
DISPLAY=:2 openbox --replace &
```

openbox 启用后 windowactivate 正常工作，但扩展快捷键仍然无法触发（见上条）。openbox 的唯一价值是支持 xdotool windowactivate，为其他场景留了可能性。

### CDP（Chrome DevTools Protocol）+ 扩展 Service Worker 自动化（方案E，首选）

**CDP 可以稳定工作**，解决了之前 version 的"CDP 绑定不可靠"问题。关键修正：

1. **必须使用非默认 `--user-data-dir`**：Chrome 的安全策略拒绝 CDP 与默认 profile 同时运行。创建专用 profile：
   ```bash
   mkdir -p ~/.config/chrome-cdp
   cp -r ~/.config/google-chrome/Default ~/.config/chrome-cdp/Default/
   ```

2. **复制扩展配置**（保留 Obsidian Web Clipper 的保存路径等设置）：
   ```bash
   EXT_ID="cnjifjpddelmedmihgijeibhnjfabmlf"
   SRC="$HOME/.config/google-chrome/Default/Local Extension Settings/$EXT_ID"
   DST="$HOME/.config/chrome-cdp/Default/Local Extension Settings/$EXT_ID"
   mkdir -p "$DST" && cp "$SRC"/* "$DST/" 2>/dev/null
   ```

3. **启动 Chrome 带 CDP**：
   ```bash
   DISPLAY=:2 google-chrome \
     --remote-debugging-port=9222 \
     --no-first-run --disable-gpu --disable-software-rasterizer \
     --user-data-dir=$HOME/.config/chrome-cdp
   ```

4. **验证**：
   ```bash
   curl -s http://localhost:9222/json/version
   ```

#### 自动化剪藏流程（CDP + 扩展 Service Worker）

最可靠的 VNC 自动化方案：不依赖 xdotool 键盘事件，而是通过 CDP 连接扩展的 Service Worker 直接调用保存函数。

**核心原理**：
1. CDP 导航到目标页面（`Page.navigate`）
2. 对 X.com 等需登录页面：用 `Network.setCookie` 注入 cookie（从 `~/.config/xfetch/session.json` 读取 auth_token + ct0）
3. 从 CDP 列表中找到扩展 Service Worker 的 WebSocket URL（`chrome-extension://cnjifjpddelmedmihgijeibhnjfabmlf/background.js`）
4. 连接 SW，通过 `Runtime.evaluate` 执行：
   ```javascript
   chrome.tabs.sendMessage(tabId, {action: "saveMarkdownToFile"})
   ```
5. 扩展的 content script 收到消息后：提取页面内容 → defuddle 解析 → 转 markdown → 触发文件下载到配置目录

**脚本位置**：`scripts/vnc-clip.py`（在 skill 目录下）

**扩展文件命名**：vnc-clip.py 触发扩展保存后，文件名由扩展的默认模板决定，格式为 `Post by @用户名 on X.md`（如 `Post by @yanhua1010 on X.md`）。不可配置，文件内容质量不受影响。 

```bash
python3 scripts/vnc-clip.py <URL>
```

该脚本会自动处理：cookie 注入、查找正确 tab、注入 content script（如未加载）、发送保存命令。

**为什么这个方案可靠**：
- `chrome.tabs.sendMessage()` 是 Chrome 扩展内部 API，不需要用户手势
- content script 的执行与 Xvfb 窗口状态无关
- 通过 CDP 注入 cookie 绕过登录页限制
- 保存路径由扩展配置（Save file 模式中的 vault path）决定，统一到 Clippings 目录

**已知限制**：
- `chrome.action.openPopup()` 保留用户手势限制，从 SW 调用会报 "Could not find an active browser window"
- 首次需复制扩展配置到 CDP profile
- CDP 需配合 openbox 同时运行（脚本会自动检查）

## Search & Clip 完整工作流

当用户说「去推特搜索关于 X 的评论比较高的文章然后剪藏」时，执行以下流程：

### 1. 搜索发现（使用方案D的搜索方法，但不用于剪藏）

```bash
# 用 xreach 搜索并排序
xreach search "obsidian web clipper" -n 30 2>&1 | python3 -c '
import json, sys
data = json.load(sys.stdin)
tweets = data.get("items", [])
tweets.sort(key=lambda t: -(t.get("likeCount",0) + t.get("retweetCount",0) + t.get("bookmarkCount",0)))
for t in tweets[:10]:
    print(f"ID: {t['id']} | 👍{t.get('likeCount',0)} 🔁{t.get('retweetCount',0)} 🔖{t.get('bookmarkCount',0)}")
    print(f'  {t.get(\"text\",\"\")[:120].replace(chr(10),\" \")}')
'
```

### 2. 获取用户信息（确认推文质量）

```bash
xreach tweet POST_ID --json
```

### 3. 剪藏（使用方案E：vnc-clip.py）

```bash
# 先确保 VNC 服务 + Chrome CDP 已启动
python3 scripts/vnc-clip.py https://x.com/username/status/POST_ID
```

### 4. 清理旧文件

如果之前用方案D（手动格式化）剪藏过同批内容扩展，删除旧文件：

```bash
rm ~/projects/wsj-second-brain/Clippings/*.md   # 方案D的保存目录
```

正确的剪藏输出路径是方案E的 `Inbox/LLM-WiKi/Raw/Clippings/`。

---

## 参考资料

- [Obsidian Web Clipper 源码](https://github.com/obsidianmd/obsidian-clipper)
- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
- `scripts/clip.py` — 原自动化剪藏脚本（bs4 + markdownify）  
- `scripts/vnc-clip.py` — VNC CDP + 扩展 SW 自动化剪藏脚本
- `references/x-article-clipping.md` — X Article 全文提取 + 剪藏到 vault 的完整流程（cookie 注入法）
- `references/xreach-tweet-clipping.md` — xreach API 推文搜索+剪藏到 vault 的工作流（本 session 新增）
- `references/cdp-direct-extraction.md` — CDP 直接 DOM 提取方案（扩展不可用时的回退方案）
