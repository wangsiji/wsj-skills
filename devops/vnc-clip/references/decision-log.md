# VNC Clip 技术决策记录

## 问题

在 VPS (Xvfb + noVNC) 上自动化 Obsidian Web Clipper 剪藏，需要处理 X.com 等需登录站点。

## 方案演进

### 方案 A：xdotool 键盘快捷键 ❌

**尝试**：`xdotool key alt+shift+o` 触发 Web Clipper 的 Quick Clip 快捷键
**失败原因**：三层叠加
1. Xvfb 无窗口管理器 → `windowactivate` 失败
2. 装 openbox 后 → `Ctrl+Shift+O` 被 Chrome 内置书签捷径拦截
3. Xvfb 下 Chrome 拒绝处理非物理键盘的扩展快捷键

### 方案 B：`chrome.action.openPopup()` ❌

**尝试**：从扩展 Service Worker 调用 `action.openPopup()`
**失败原因**：Chrome 需要用户手势（user gesture），Xvfb 无"活跃窗口"概念

### 方案 C：CDP 直接 DOM 提取 ⚠️

**尝试**：`Runtime.evaluate` 在页面发 JS 提取内容
**结果**：公开页 OK，X.com 需 cookie → 注入后提取但 DOM 噪声大
**放弃原因**：质量不如 Defuddle 引擎

### 方案 D：CDP + 扩展 SW 消息 ✅

**核心洞察**：content script 侦听 `chrome.runtime.onMessage`，扩展 SW 可通过 `chrome.tabs.sendMessage(tabId, {action: "saveMarkdownToFile"})` 直接触发保存，完全绕过 popup。

**流程**：CDP 导航 → cookie 注入 → 连 SW → `tabs.sendMessage("saveMarkdownToFile")` → content script Defuddle 提取 → 自动保存

## 关键教训

| 教训 | 详情 |
|------|------|
| Xvfb 下不要模拟用户交互 | 优先 API/协议级自动化 |
| 扩展自动化的优先级 | `tabs.sendMessage` > `openPopup` > `commands.onCommand` > xdotool |
| CDP 需非默认 `--user-data-dir` | Chrome 安全策略，默认 profile 不让绑 debug port |
| 扩展配置在 LevelDB | `Local Extension Settings/<id>/`，cp 时需 Chrome 不锁定 |
| pip cache 是磁盘杀手 | 曾积累 9.5GB，撑爆 Syncthing |
