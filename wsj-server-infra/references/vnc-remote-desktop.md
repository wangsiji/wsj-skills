# VNC 远程桌面

> 服务器 VNC 桌面（noVNC + x11vnc + Xvfb）启动、验证、排错。主文件见 `SKILL.md` 任务路由 D。

## 4.1 启动（已知可用配置）

```bash
# 1. 清理旧进程
pkill Xvfb 2>/dev/null; pkill x11vnc 2>/dev/null; pkill websockify 2>/dev/null; sleep 1

# 2. Xvfb 虚拟显示器
Xvfb :2 -screen 0 1920x1080x24 &
sleep 1

# 3. Openbox 窗口管理器（Chrome 需要）
DISPLAY=:2 openbox --replace &

# 4. x11vnc（-noshm 关键：容器/VPS 环境避免 MIT-SHM 错误）
x11vnc -display :2 -localhost -forever -shared -rfbauth ~/.vnc/passwd -noshm &

# 5. noVNC websockify
websockify --web=/home/wangsiji/noVNC 6080 localhost:5900 &
```

访问：`http://VPS_IP:6080/vnc.html`（密码：`test1234`）

## 4.2 设置密码

```bash
echo -n "新密码" | x11vnc -storepasswd "新密码" ~/.vnc/passwd
```

## 4.3 Chrome CDP 启动（用于 Obsidian Web Clipper）

```bash
# 接在上面的启动顺序之后
DISPLAY=:2 google-chrome \
  --remote-debugging-port=9222 \
  --no-first-run --disable-gpu --disable-software-rasterizer \
  --user-data-dir=$HOME/.config/chrome-cdp &

# 验证
curl -s http://127.0.0.1:9222/json/version
```

## 4.4 验证

```bash
# 进程
ps aux | grep -E 'Xvfb|x11vnc|websockify' | grep -v grep
# 端口
ss -tlnp | grep -E '6080|5900'
# noVNC HTTP
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html
# 期望: 200
```

## 4.5 常见故障

| 症状 | 根因 | 解决 |
|------|------|------|
| MIT-SHM 错误 | 容器/VPS 无共享内存 | x11vnc 加 `-noshm` |
| Xvfb 权限错误 | /tmp/.X11-unix 不存在 | `mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix` |
| Display 冲突 | 端口被占 | 换 `:3` 或 `pkill Xvfb` |
| 黑屏有鼠标 | 无桌面环境 | Xvfb 有显示但无可渲染内容，需 openbox 或 x-window-manager |
| Chrome 崩溃 | Xvfb 无 WM | `openbox --replace &` 先启动 |
