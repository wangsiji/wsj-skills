# xdotool + VNC Desktop Automation

在 noVNC/Xvfb 虚拟桌面中用 xdotool 和 ImageMagick 程序化操作 GUI 应用。

## 基础命令

```bash
# 列出所有窗口
DISPLAY=:2 xdotool search --name ""
# 获取窗口详细信息（名称、位置、大小）
DISPLAY=:2 xdotool getwindowgeometry <window_id>
DISPLAY=:2 xdotool getwindowname <window_id>

# 键盘输入（先激活页面）
DISPLAY=:2 xdotool key ctrl+t           # 新标签页
DISPLAY=:2 xdotool type "https://..."   # 输入文本
DISPLAY=:2 xdotool key Return           # 回车

# 鼠标操作
DISPLAY=:2 xdotool mousemove X Y       # 移动鼠标
DISPLAY=:2 xdotool click 1             # 左键点击

# Tab 键导航（在弹窗/表单中跳到下一元素）
DISPLAY=:2 xdotool key Tab

# 快捷键
DISPLAY=:2 xdotool key ctrl+shift+O    # Ctrl+Shift+O

# 截图
DISPLAY=:2 import -window root /tmp/screenshot.png
```

## 查找 Chrome 窗口

Chrome 在 Xvfb 中可能有多个子窗口，先找主窗口：

```bash
# 列举所有窗口并逐一查看名称和尺寸（最可靠的方法）
DISPLAY=:2 xdotool search --name "" | while read id; do
  name=$(DISPLAY=:2 xdotool getwindowname "$id" 2>/dev/null)
  geo=$(DISPLAY=:2 xdotool getwindowgeometry "$id" 2>/dev/null | grep Geometry)
  echo "ID=$id Name='$name' $geo"
done

# 主 Chrome 窗口一般 1280x900（你指定的 window-size），可以这样过滤
# 用 --name "Chrome" 不一定能找到，因为标签页标题是网站名不是 "Chrome"
```

## Chrome 窗口查找与多实例\n\nChrome 在 Xvfb 中可能会有多个子窗口。要定位主窗口，遍历所有窗口并检查尺寸：\n\n```bash\nDISPLAY=:2 xdotool search --name \"\" | while read id; do\n  name=$(DISPLAY=:2 xdotool getwindowname \"$id\" 2>/dev/null)\n  geo=$(DISPLAY=:2 xdotool getwindowgeometry \"$id\" 2>/dev/null | grep Geometry)\n  if echo \"$geo\" | grep -q \"1280x\"; then\n    echo \"Main window: ID=$id Name='$name' $geo\"\n  fi\ndone\n```\n\n主 Chrome 窗口通常是你通过 `--window-size=1280,900` 指定的那个。其他子窗口（如 `google-chrome` 名 10x10）是后台进程窗口，忽略即可。\n\n### 键盘快捷键说明\n\n对于 Obsidian Web Clipper 扩展，有两个不同的键盘快捷键，触发不同行为：\n\n| 快捷键 | 功能 | 效果 |\n|--------|------|------|\n| **Ctrl+Shift+O** | `_execute_action` | 打开 Web Clipper 弹窗（popup），手动选择模板/行为后保存 |\n| **Alt+Shift+O** | `quick_clip` | 直接剪藏，不弹窗，使用默认设置保存 |\n\n用 xdotool 触发：\n```bash\n# 打开弹窗\nDISPLAY=:2 xdotool key --window $WIN_ID --clearmodifiers ctrl+shift+o\n\n# 快速剪藏（使用默认设置）\nDISPLAY=:2 xdotool key --window $WIN_ID --clearmodifiers alt+shift+o\n```\n\n弹窗出现后的交互（优先用键盘）：\n```bash\n# Tab 导航到保存按钮（通常需要 5-8 次 Tab）\nfor i in $(seq 1 8); do\n  DISPLAY=:2 xdotool key --window $POPUP_WIN Tab\n  sleep 0.1\ndone\nDISPLAY=:2 xdotool key --window $POPUP_WIN Return\n```\n\n### 排查 Chrome 启动失败\n\n如果 Chrome 启动后屏幕只显示一个小尺寸截图（<100KB）或窗口标题显示 \"Bookmarks - Google Chrome\"，通常是以下原因之一：\n\n1. **锁文件残留** — 同一 `--user-data-dir` 上有另一个 Chrome 进程。杀掉并清理 Singleton* 文件\n2. **多个 Chrome 实例冲突** — `pkill chrome` 可能不够，需要确认所有子进程（特别是 crashpad handler）都死了\n3. **数据库锁定** — 日志中出现 `database is locked` → 同上，锁文件问题\n\n## 已知限制与坑

### 窗口激活不可用
Xvfb 的 window manager 不支持 `_NET_ACTIVE_WINDOW` 协议，`xdotool windowactivate` 会报错：
```
Your windowmanager claims not to support _NET_ACTIVE_WINDOW
```
**解决**：不依赖激活，直接发键盘事件（Xvfb 允许向任何窗口发 key events）

### 键盘事件在 Chrome 中不可靠

`xdotool key` / `xdotool type` **并不能可靠地向 Chrome 地址栏发送按键**，即使 `windowfocus` 成功。
实测发现：Alt+D/Ctrl+L 聚焦地址栏后，`xdotool type` 输入的 URL 未被接收，窗口标题始终显示新标签页内容未改变。

**原因推测**：
- Chrome 在 Xvfb 下可能有输入焦点管理问题
- Chrome 的地址栏可能使用非标准输入处理
- `xdotool key --window $WID` 和 `xdotool key`（全局）都不生效

**结论**：不要依赖 xdotool 自动化 Chrome 的页面导航或扩展操作。
VNC Chrome 只适合用户手动操作。自动化剪藏用 Hermes 浏览器（`browser_navigate` + `browser_console`）。

### Chrome 扩展快捷键
Web Clipper 扩展快捷键 `Ctrl+Shift+O` 通过 xdotool 可以触发弹窗，但：
- 必须在正确的 Chrome 窗口上（可以通过 `key ctrl+t` 先确认 Chrome 是活跃的）
- 弹窗中的按钮点击建议用 Tab 导航代替鼠标坐标

### 扩展设置持久化（通过 CDP 配置 chrome.storage）

当扩展通过 `--load-extension` 加载时，其设置（如 Save file 模式）默认存在临时 `chrome.storage` 中。要持久化配置，使用 Chrome DevTools Protocol (CDP) 直接操作扩展的 storage API。

**步骤：**

1. 启动 Chrome 带远程调试端口（必须用非默认 user-data-dir）：
   ```bash
   cp -a ~/.config/google-chrome /tmp/persistent-profile
   rm -f /tmp/persistent-profile/Singleton*
   
   DISPLAY=:2 google-chrome \
     --user-data-dir=/tmp/persistent-profile \
     --load-extension=/path/to/extension \
     --remote-debugging-port=9225 \
     --remote-allow-origins=* \
     "https://target-url.com" &
   ```

2. 通过 CDP 找到扩展的 service worker：
   ```python
   import json, urllib.request
   
   with urllib.request.urlopen('http://127.0.0.1:9225/json') as resp:
       targets = json.loads(resp.read())
   
   for t in targets:
       if 'background.js' in t['url'] and 'EXTENSION_ID' in t['url']:
           bg_ws = t['webSocketDebuggerUrl']
   ```

3. 连接 service worker 并设置 chrome.storage：
   ```python
   import websocket, json
   
   ws = websocket.create_connection(bg_ws)
   
   # 获取当前设置
   ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 
       'expression': 'await chrome.storage.sync.set({"saveBehavior": "saveFile"})'}))
   ```

**关键点：**
- `--remote-debugging-port` 被 Chrome 拒绝在 `~/.config/google-chrome` 上工作（视为默认目录）。必须复制到 `/tmp/` 或用其他路径
- 扩展的 service worker 在 CDP 中表现为 `type=service_worker` 的 target，其 URL 包含 `chrome-extension://EXTENSION_ID/background.js`
- Chrome 的 storage API（`chrome.storage.sync/local`）只能从扩展上下文（service worker / background page）访问，不能从普通页面
- 设置后最好验证：`const check = await chrome.storage.sync.get('saveBehavior')`

**实际案例 — Obsidian Web Clipper 设置 Save file 模式：**
扩展 ID 可通过 `chrome://extensions` 或在 `Preferences` 的 `extensions.settings` 中找到。设置 key 为 `saveBehavior`，值 `saveFile`。UI 元素 ID 为 `save-behavior-dropdown`。

### --load-extension 与远程调试
- `--load-extension` 加载的扩展 ID 由 Chrome 动态生成（不在 Preferences 中）
- 要获取扩展 ID / 配置扩展，需要用 `--remote-debugging-port` + `--user-data-dir=<新目录>`
- `--remote-allow-origins=*` 允许外部 WebSocket 客户端连接 CDP
- 在同一 user-data-dir 上不能同时运行两个 Chrome 实例（"Opening in existing browser session"）

**远程调试端口限制**：Chrome 拒绝在 `~/.config/google-chrome`（被视为"默认"数据目录）上启用 `--remote-debugging-port`。日志会报：
```
DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.
```
即使你显式传了 `--user-data-dir=/home/wangsiji/.config/google-chrome` 也一样。解决：用 `--user-data-dir=/tmp/chrome-debug-profile`（临时目录）调试，或 `cp -a ~/.config/google-chrome /tmp/persistent-profile` 克隆一份（注意区分锁文件）。

### 使用永久 Chrome 配置目录（持久化登录态）

默认情况下 VPS 上启动 Chrome 会使用临时用户数据目录（`/tmp/.com.google.Chrome.*`），关掉后登录态、扩展设置全部丢失。

要持久化登录态，需要指定永久配置目录（即用户的正式 Chrome 配置文件 `~/.config/google-chrome`）：

```bash
# 首次启动（确保没有其他 Chrome 进程在跑）
pkill -f "chrome.*--user-data-dir" 2>/dev/null
sleep 1

# 清理锁文件（关键！同一 user-data-dir 不能有两个 Chrome 实例）
rm -f ~/.config/google-chrome/SingletonLock \
      ~/.config/google-chrome/SingletonSocket \
      ~/.config/google-chrome/SingletonCookie

# 用永久配置启动
DISPLAY=:2 google-chrome \
  --user-data-dir=/home/wangsiji/.config/google-chrome \
  --load-extension=/tmp/obsidian-clipper/dist \
  --no-first-run \
  --new-window \
  --window-size=1280,900 \
  "https://x.com/..." \
  &>/tmp/chrome_vnc.log &
```

**注意事项：**
- `--user-data-dir` 指向 `~/.config/google-chrome`（用户的正式 Chrome 配置）后，登录态（X/Twitter、Google 账号等）、扩展设置（如 Obsidian Web Clipper 的 Save file 模式）都会保留
- **锁文件（SingletonLock/SingletonSocket/SingletonCookie）**：同一 user-data-dir 只能由一个 Chrome 进程持有。如果之前启动过 Chrome 没有正常退出，残留的锁文件会导致新实例报 `"Opening in existing browser session."` 并拒绝启动。必须先清理
- `--new-window`：在已有 Chrome 会话仍在时打开新窗口（但锁文件问题会导致该失败）。恢复桌面后建议先全杀再启动
- 首次启动用永久配置目录可能需要等待 5-10 秒初始化
- WebGL 相关的 `blocklisted` 错误在无 GPU 的 VPS 环境下是正常的，不影响功能

**覆盖已有 Chrome 会话的流程：**
```bash
# Step 1: 找到并杀掉所有 chrome 主进程
pkill chrome                  # 杀主进程 + crashpad 处理器（注意！pkill -f "google-chrome" 不行，二进制名为 "chrome"）
sleep 2

# Step 2: 清理锁文件
rm -f ~/.config/google-chrome/Singleton*

# Step 3: 启动新实例
DISPLAY=:2 google-chrome \
  --user-data-dir=/home/wangsiji/.config/google-chrome \
  --load-extension=/tmp/obsidian-clipper/dist \
  --no-first-run --new-window --window-size=1280,900 \
  "https://x.com/" \
  &>/tmp/chrome_vnc.log &

# Step 4: 验证（检查日志）
sleep 5
cat /tmp/chrome_vnc.log  # 不应该出现 "Opening in existing browser session"
```

**何时用永久配置 vs 临时配置：**
- **永久配置**：当你需要持续使用同一登录态（X 帖子、扩展配置如 Save file 模式）、跨会话保留浏览器设置
- **临时配置**：一次性测试、不会持久化的操作、不想污染用户正式 Chrome 配置时

### 截图技巧
```bash
# 全屏截图
DISPLAY=:2 import -window root /tmp/vnc_screenshot.png

# 确保安装了 imagemagick
which import || sudo apt-get install -y imagemagick
```

## 典型工作流：自动化 Chrome 扩展操作

```bash
# 1. 启动 Chrome（带扩展）
DISPLAY=:2 google-chrome-stable --no-sandbox --window-size=1280,800 \
  --load-extension=/path/to/extension &

sleep 5

# 2. 导航到目标页面
DISPLAY=:2 xdotool key ctrl+t
sleep 0.5
DISPLAY=:2 xdotool type "https://target-url.com"
sleep 0.3
DISPLAY=:2 xdotool key Return

sleep 5  # 等待页面加载

# 3. 触发扩展
DISPLAY=:2 xdotool key ctrl+shift+O

sleep 2

# 4. Tab 导航到保存按钮
for i in $(seq 1 8); do
  DISPLAY=:2 xdotool key Tab
  sleep 0.1
done

# 5. 确认保存
DISPLAY=:2 xdotool key Return
```
