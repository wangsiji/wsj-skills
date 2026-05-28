---
name: vps-remote-desktop
description: noVNC + Xvfb + x11vnc 搭建可从浏览器访问的 VPS 图形桌面，以及常见故障排查
category: devops
triggers:
  - "noVNC 打不开了"
  - "VNC 没了"
  - "浏览器访问 VPS 桌面"
  - "Xvfb 报错"
  - "x11vnc 连接不上"
---

# VPS 远程桌面（noVNC + Xvfb + x11vnc）

## 前提条件

```bash
# x11vnc 可能未预装，需要单独安装
which x11vnc || sudo apt-get install -y x11vnc

# websockify 和 noVNC 一般已有
which websockify  # /usr/bin/websockify
ls /home/wangsiji/noVNC/vnc.html  # noVNC 源码目录
```

## VNC 密码

密码文件：`~/.vnc/passwd`，当前密码：`test1234`
设置新密码：`echo -n "新密码" | x11vnc -storepasswd "新密码" ~/.vnc/passwd`

## 快速恢复（已知可用配置）

```bash
# 1. 清理旧进程
pkill Xvfb 2>/dev/null; pkill x11vnc 2>/dev/null; pkill websockify 2>/dev/null; sleep 1

# 2. 启动 Xvfb 虚拟显示器（用 :2 避开旧状态）
Xvfb :2 -screen 0 1920x1080x24 &

# 3. 启动 x11vnc（-noshm 关键：容器/ VPS 环境避免 MIT-SHM 错误）
sudo x11vnc -display :2 -localhost -forever -shared -rfbauth ~/.vnc/passwd -noshm &

# 4. 启动 websockify 代理
websockify --web=/home/wangsiji/noVNC 6080 localhost:5900 &
```

访问：`http://你的VPSIP:6080/vnc.html`

---

## 关键陷阱

### MIT-SHM 错误
**症状**：`X Error of failed request: BadAccess ... Major opcode 130 (MIT-SHM)`
**原因**：共享内存段在容器/VPS 环境中不可用
**解决**：x11vnc 加 `-noshm` 参数，或 Xvfb 加 `-shm no`（如果支持）

### Xvfb 权限问题
**症状**：`_XSERVTransmkdir: ERROR: euid != 0, directory /tmp/.X11-unix will not be created`
**解决**：手动创建目录 `mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix`

### Display 编号冲突
**症状**：`Address already in use`（5900 端口或 X display 被占用）
**解决**：换用不同的 display 编号（:2、:3），或先 `pkill Xvfb`

### 黑屏问题（无桌面环境）
**症状**：noVNC 连接成功（能看到鼠标移动），但屏幕全黑
**原因**：Xvfb 运行正常，但里面没有启动任何桌面环境（x-window-manager、GNOME 等），X server 在跑但没有可渲染的内容
**说明**：icloud-for-linux 等 snap GUI 应用即使装上了也需要完整的图形桌面（x-terminal-emulator、x-window-manager、X session），纯 Xvfb 不够用
**不要在 VPS 上花时间调试这类桌面应用的完整渲染**。如果需要跑 GUI 应用，正确的路径是搭建完整桌面环境（GNOME/XFCE via VNC），而不是只用 Xvfb。

---

## systemd 服务化（持久化）

将以下文件写入 `~/.config/systemd/user/novnc.service`：

```ini
[Unit]
Description=noVNC Web Terminal
After=network.target

[Service]
ExecStart=/usr/bin/websockify --web=/home/wangsiji/noVNC 6080 localhost:5900
Restart=always
User=wangsiji

[Install]
WantedBy=default.target
```

x11vnc 和 Xvfb 需要另外的服务文件。完整 systemd 配置略（见 `references/novnc-systemd.md`）。

---

## iCloud 备忘录等桌面应用

icloud-for-linux snap 包可以安装，但它在 **无图形桌面环境** 的 VPS 上无法正常工作。详见 `references/icloud-on-linux.md`（syncthing-setup 技能目录下）。简述：

- iCloud Drive：iCloud 没有给 Linux 的 WebDAV 接口，无法挂载
- icloud-for-linux：是 Qt 图形应用，需要完整桌面环境，VPS 不适用
- 替代方案：iPhone/Mac 原生访问 iCloud，VPS 用 Syncthing 同步文件

---

## VPS 的 systemd 调优

VPS 环境（特别是 HostPapa/RackNerd 等廉价 VPS）的 systemd 配置常有兼容性问题。常见情况及解决方案见 `references/systemd-common-issues.md`。

最常遇到的是 **216/GROUP** 错误：当 `/etc/nsswitch.conf` 中 `group:` 行包含 `winbind` 而 winbind 未运行时，`systemctl --user` 启动的服务会失败。解决方案：改用系统级 service + 显式 `User=` + 空 `SupplementaryGroups=`。

## xdotool 桌面自动化

在 Xvfb 虚拟桌面中用 xdotool/ImageMagick 程序化操作 GUI 应用（如触发 Chrome 扩展、截图等），详见 `references/xdotool-vnc-automation.md`。

**核心限制**：Xvfb 不支持 `_NET_ACTIVE_WINDOW`，`windowactivate` 不可用。`windowfocus` + `mousemove --sync` + `click` 可以定位和点击窗口内元素，但键盘快捷键（`ctrl+shift+s` 等）无法送达 Chrome 扩展。

**已验证在 VNC Chrome 1288×851 窗口中可用 xdotool 操作：**
- 地址栏导航：`mousemove --sync 700 20` → `click 1` → `key ctrl+a` → `type "URL"` → `key Return`
- 扩展菜单：`mousemove --sync 1230 18` → `click 1` 点出拼图图标
- 弹窗弹出：在扩展菜单中点第一个扩展项

**不能用：**
- 键盘快捷键触发扩展（Ctrl+Shift+S）
- 弹窗内精确按钮点击（无视觉反馈，盲猜坐标不可靠）

## 验证步骤

```bash
# 检查进程
ps aux | grep -E 'Xvfb|x11vnc|websockify' | grep -v grep

# 检查端口
ss -tlnp | grep -E '6080|5900'

# 测试 noVNC HTTP
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html
# 期望输出: 200
```
