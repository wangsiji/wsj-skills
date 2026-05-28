# 原型部署与 Telegram 分享工作流

## 快速部署 HTML 原型

### Step 1: nginx（推荐）

```bash
# 复制到网站根目录（需要 sudo）
sudo cp /home/wangsiji/projects/miniprogram/preview.html /var/www/html/preview.html

# 访问地址
# http://192.3.16.123/preview.html
```

**注意**：nginx 运行在 192.3.16.123:80，`/var/www/html/` 是 root 目录。

**⚠️ 上线前清理旧进程**：VPS 重启后可能残留指向已删除目录的 Python HTTP 服务器。
```bash
ps aux | grep "http.server" | grep -v grep
kill <PID>
```

### Step 2: python http.server（备选，无 sudo 时）

```bash
cd /home/wangsiji/projects/miniprogram
python3 -m http.server 8787
# 访问：http://192.3.16.123:8787/preview.html
# ⚠️ 目录路径必须存在，否则返回 404
# ⚠️ 用 background=true 启动
```

## 移动端 CSS 陷阱：fixed tab bar 不显示

**问题**：`.app { height: 100% }` + `.page { flex: 1 }` 时，移动端浏览器地址栏会压缩 `100vh`，
导致 `position: fixed; bottom: 0` 的 tab bar 被推出可视区。

**正确布局**：
```css
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;        /* 用 dvh，不用 vh */
  position: fixed;        /* 锚定在视口 */
  top: 0; left: 0;
  right: 0; bottom: 0;
}
.page {
  flex: 1;
  overflow-y: auto;
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
}
.tab-bar {
  position: fixed;
  bottom: 0;
  bottom: env(safe-area-inset-bottom, 0px);
  z-index: 100;
}
```

**要点**：
- app 用 `position: fixed` + `100dvh`（dynamic viewport height），不是 `100vh`
- tab-bar 单独再设 `env(safe-area-inset-bottom)` 兼容 iPhone 刘海
- 用 `100dvh` 替代 `100vh`，移动端地址栏出现/隐藏时自动调整

## 发送 Telegram

### 发送文件（预览原型）

```python
send_message(
    message="MEDIA:/home/wangsiji/projects/miniprogram/preview.html",
    target="telegram:wang siji"
)
```

### 发送链接

```python
send_message(
    message="http://192.3.16.123/preview.html",
    target="telegram:wang siji"
)
```

### Telegram chat_id

- wang siji DM: `7128007362`
- 发送格式: `telegram:wang siji` 或直接用 chat_id

## emoji 图标在某些环境下是黑色/透明的

**症状**：CSS 正确、DOM 元素存在，但渲染出来完全看不见。
像素分析发现 `avg brightness ≈ 11/255`，和背景几乎同色。

**原因**：chromium headless 的 emoji 渲染依赖系统字体，某些 Unicode 字符（⏱🧰👤◉⬡）在无头模式/微信 webview 下字体解析失败，显示为黑色或透明。

**修复**：tab-bar 用**高对比度白色背景 + 紫色边框**，图标用 `<text>` 备选或纯色 SVG，不要只用 emoji。

## DNS 问题记录

**wangcc.cc 当前解析**

```
wangcc.cc A 185.53.179.128  ← 错误IP，第三方托管页面的IP
```

**VPS 实际 IP**: `192.3.16.123`

如需用域名访问，需要把 DNS A 记录改成 192.3.16.123。

当前阶段直接用 IP 访问最可靠。
