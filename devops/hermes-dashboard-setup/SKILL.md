---
name: hermes-dashboard-setup
description: 部署 Hermes Dashboard + nginx反代 + HTTPS + 基本认证。systemd 服务管理、SSL 证书、Host header 兼容。适合普通用户，不含专业术语。
---

# Hermes Dashboard 远程访问配置指南

用 nginx 给 Hermes Dashboard 套上密码保护和 HTTPS 加密，绑定自己的域名，从任何地方用浏览器安全访问。

## 你需要什么

- 一台 VPS（已装好 Hermes Agent）
- 一个域名（比如 `example.com`）
- 基本 Linux 操作能力（会敲命令就行）

## 第一步：启动 Hermes Dashboard

Hermes 自带一个网页版控制面板（Dashboard），默认在 `127.0.0.1:9119` 上运行。

```bash
# 启动
hermes dashboard

# 查看状态
hermes dashboard --status

# 停止
hermes dashboard --stop
```

测试是否启动成功：

```bash
curl http://127.0.0.1:9119/
```

能看到 HTML 返回就算成功。

## 第二步：配置开机自启

⚠️ **不要用 user-level service**（某些 VPS 因 `/etc/nsswitch.conf` 含 `winbind` 导致 status=216/GROUP）。

写一个启动脚本（替换 `你的用户名`）：

```bash
cat > ~/.local/bin/hermes-dashboard.sh << 'EOF'
#!/bin/bash
cd /home/你的用户名
source /home/你的用户名/.hermes/hermes-agent/venv/bin/activate
exec python -m hermes_cli.main dashboard
EOF
chmod +x ~/.local/bin/hermes-dashboard.sh
```

创建 systemd 服务：

```bash
sudo tee /etc/systemd/system/hermes-dashboard.service << 'EOF'
[Unit]
Description=Hermes Agent Dashboard
After=network.target

[Service]
Type=simple
User=你的用户名
ExecStart=/home/你的用户名/.local/bin/hermes-dashboard.sh
WorkingDirectory=/home/你的用户名
Restart=always
RestartSec=10
SupplementaryGroups=

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now hermes-dashboard.service

> **为什么用 `Restart=always` 而不是 `Restart=on-failure`？**  
> `hermes update` 会优雅关闭 Dashboard 进程（exit code 0），`on-failure` 不会拉起。改为 `always` 后任何退出都会自动重启，update 后等几秒就恢复了。
```

验证：

```bash
sudo systemctl status hermes-dashboard.service
```

看到 `active (running)` 就对了。

## 第三步：设置域名 DNS

去你的域名管理后台（阿里云/腾讯云/Cloudflare 等），加一条 **A 记录**：

```
你的域名 → 你的 VPS 公网 IP
```

等几分钟让它生效，检查：

```bash
dig +short 你的域名 @8.8.8.8
```

返回你的 VPS IP 就算生效了。

## 第四步：安装工具

```bash
sudo apt-get install -y nginx apache2-utils certbot python3-certbot-nginx
```

## 第五步：设置密码

```bash
sudo htpasswd -c /etc/nginx/.htpasswd 你的用户名
```

## 第六步：写 nginx 配置

```bash
sudo tee /etc/nginx/sites-available/hermes-dashboard << 'EOF'
server {
    server_name 你的域名;

    auth_basic "Hermes Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:9119;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host "127.0.0.1:9119";  # ⚠️ 必须这样写！dashboard 校验 Host header
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

⚠️ **关键坑**：`proxy_set_header Host` 必须设成 `"127.0.0.1:9119"`，不能传原始域名或 `$host`。Hermes dashboard 内部校验 Host header，传域名会返回 `Invalid Host header`。

## 第七步：配置 HTTPS（免费证书）

```bash
sudo certbot --nginx -d 你的域名 --agree-tos --email 你的邮箱
```

证书 90 天有效，certbot 会自动续期，不用管。

## 第八步：测试

```bash
# 浏览器打开 https://你的域名，输入用户名和密码

# 命令行测试
curl -s -u "用户名:密码" https://你的域名 | head -5
```
不带密码应该返回 401，带密码返回 200 和 HTML 页面。

---

## 进阶：Dashboard 部署到子路径（非根域名）

如果不想独占域名，可以把 Dashboard 放在子路径（如 `/hermes/`），根路径用做其他用途（如静态站点）：

```nginx
# 根路径 → 跳转到公开页面
location = / {
    auth_basic off;
    return 302 /my-public-page/;
}

# 公开静态站点
location /my-public-page/ {
    auth_basic off;
    alias /var/www/my-public-page/;
    try_files $uri $uri/ /my-public-page/index.html =404;
}

# Dashboard 在子路径
location /hermes/ {
    auth_basic "Hermes Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://127.0.0.1:9119/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host "127.0.0.1:9119";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /hermes;  # 告诉 Dashboard 它在子路径

    proxy_read_timeout 86400;
}
```

⚠️ **子路径部署的三个关键点**：

1. `proxy_pass` 的 URL 末尾必须带 `/`（如 `http://127.0.0.1:9119/`），这样 nginx 会把 `/hermes/` 前缀剥离后传给后端
2. `proxy_set_header X-Forwarded-Prefix /hermes;` — 显式告诉 Dashboard 它的路径前缀，让内部链接生成正确
3. **根路径的 redirect location 必须有 `auth_basic off`** — 如果你的 `auth_basic` 设在了 `server` 块级别（影响所有 location），redirect-only 的 location（如 `location = / { return 302 ... }`）不会自动跳过认证，需要显式关闭

**⚠️ 另一个常见坑**：`sites-enabled/` 里的配置文件可能**不是**从 `sites-available/` 的软链，而是一个独立的文件。修改后务必直接编辑或覆盖 `sites-enabled/` 下的文件（或在 `sites-available/` 改完后做软链替换），否则 `nginx -t` 通过但实际不会生效。

---

## 进阶：部署第三方 Hermes Web UI（Hermes Web UI）

除了官方 Dashboard，还有第三方社区开发的 Web 管理面板（如 [EKKOLearnAI/hermes-web-ui](https://github.com/EKKOLearnAI/hermes-web-ui) 6.3k⭐），功能更丰富（平台配置、用量分析、定时任务、Web 终端、文件管理等）。

### 安装

```bash
npm install -g hermes-web-ui
```

> 详细的部署记录和故障排查见 `references/hermes-web-ui-deployment.md`。

#### ⚠️ 前提：Node.js 版本要求

hermes-web-ui 依赖 `node:sqlite` 内置模块（Node.js 22.5.0+）。**系统自带的 Node.js（常见 v18/v20）不支持。**

```bash
# 检测是否兼容
node -e "require('node:sqlite')" 2>&1 || echo "❌ 需要 Node 22.5.0+"
```

**修复：** 用 nvm 安装并使用 v22+：

```bash
# 装 nvm（如未装）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 安装并使用 Node 22
nvm install 22
nvm use --delete-prefix 22 --silent
```

systemd service 的 `ExecStart` 需指向 nvm 的 Node 路径（如 `/home/用户名/.nvm/versions/node/v22.22.0/bin/node`）。

### ⚠️ 关键：Gateway 冲突处理

hermes-web-ui 启动时自带 GatewayManager，会自动尝试 `hermes gateway start`。如果 Hermes 的 gateway 已经作为 systemd 服务运行，这个调用会超时或冲突，导致 Web UI 卡在初始化阶段无法监听端口。

**解决方案：设置 `UPSTREAM` 环境变量**，跳过 gateway 自启逻辑，直接指向已运行的 gateway：

```bash
# 直接运行
PORT=8648 UPSTREAM=http://127.0.0.1:8642 /usr/bin/node /path/to/hermes-web-ui/dist/server/index.js

# 或在 systemd service 中设置 Environment
```

`UPSTREAM` 指向运行中的 Hermes gateway 地址（默认 `http://127.0.0.1:8642`）。

### systemd 服务（user-level）

官方 Dashboard 推荐 system-level service，但 hermes-web-ui 是 Node.js 应用，更适合 user-level service 管理：

```bash
# ~/.config/systemd/user/hermes-webui.service
[Unit]
Description=Hermes Web UI - Full-featured web dashboard
After=network.target hermes-gateway.service

[Service]
Type=simple
ExecStart=/usr/bin/node /home/用户名/.npm-global/lib/node_modules/hermes-web-ui/dist/server/index.js
Restart=on-failure
RestartSec=5
Environment=PORT=8648
Environment=UPSTREAM=http://127.0.0.1:8642
Environment=NODE_PATH=/home/用户名/.npm-global/lib/node_modules
Environment=PATH=/home/用户名/.npm-global/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
```

启用：

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-webui.service
```

### nginx 反代配置（同一域名多路径）

假设已有 Dashboard 在 `/hermes/`、静态站在 `/feed/`，再加 `/webui/`：

```nginx
# Web UI — 第三方全功能面板（自带登录，不需要 nginx auth）
location /webui/ {
    auth_basic off;

    proxy_pass http://127.0.0.1:8648/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;               # Web UI 不校验 Host header
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}

# ⚠️ SPA 路径前缀坑：Web UI 是 Vue SPA，JS/CSS/API 路径是绝对路径
# （如 /assets/js/index-xxx.js, /api/hermes/sessions/...），不受 /webui/ 前缀保护。
# 访问 /webui/ 时加载了 HTML，但浏览器请求 /assets/js/... 找不到资源 → 白屏。
# 修复：额外代理这些根路径到同一个后端。
location ~ ^/(assets|api|favicon\.ico|socket\.io|upload|webhook|health|terminal) {
    auth_basic off;
    proxy_pass http://127.0.0.1:8648;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
    proxy_redirect off;
}
```

区别于 Dashboard（需 `Host "127.0.0.1:9119"`），Web UI 接受真实域名，直接传 `$host` 即可。

### 验证

| 检查项 | 命令 |
|--------|------|
| 服务状态 | `systemctl --user status hermes-webui.service` |
| 本地连通 | `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8648/` → 200 |
| nginx 反代 | `curl -s -u "用户:密码" https://域名/webui/ \| head -5` |
| 是否影响原有服务 | `curl -s http://127.0.0.1:8642/health` → `{"status":"ok"}` |

### 登录

首次访问后，hermes-web-ui 会生成一个 auth token（在 server.log 可见），也支持默认账号 `admin / 123456` 登录。

### 最终验证清单（每次部署/修改后必跑）

**这一节是从「你验证没问题再发给我」这个教训里长出来的。** 每次改完配置，按顺序跑一遍，全部通过再跟用户说完成了。

```bash
# 1. 服务活着
systemctl --user status hermes-webui.service --no-pager | grep -q "active (running)" && echo "✅ Service running" || echo "❌ Service dead"

# 2. 本地端口响应
curl -s -o /dev/null -w "✅ Local port: %{http_code}\n" http://127.0.0.1:8648/

# 3. JS 资源可加载（SPA 路径前缀问题检测）
curl -s -o /dev/null -w "✅ JS: %{http_code}\n" https://域名/assets/js/index-*.js

# 4. API 可用
curl -s https://域名/api/auth/status | grep -q "hasPasswordLogin" && echo "✅ API responds" || echo "❌ API down"

# 5. nginx 反代通（不带 auth 应返回 200 和 HTML）
curl -s --resolve 域名:443:127.0.0.1 https://域名/webui/ | grep -q "app" && echo "✅ nginx proxy OK" || echo "❌ nginx proxy broken"

# 6. 已有服务不受影响
curl -s http://127.0.0.1:8642/health | grep -q '"status":"ok"' && echo "✅ Gateway alive" || echo "❌ Gateway down"
curl -s -o /dev/null -w "✅ Dashboard: %{http_code}\n" http://127.0.0.1:9119/
```

### hermes-web-ui 常见故障排查

| 症状 | 根因 | 解决 |
|------|------|------|
| `ERR_UNKNOWN_BUILTIN_MODULE: node:sqlite` | Node.js < 22.5.0 | 用 nvm 安装 Node 22+，ExecStart 指向 nvm 路径 |
| `EADDRINUSE: address already in use` | 旧进程仍占用 8648 端口 | `kill` 旧进程或 `fuser -k 8648/tcp` 后再启动 |
| systemd 持续重启（restart counter > 10） | service 频繁失败导致 systemd 限制重启频率 | `systemctl --user reset-failed hermes-webui.service` 清除计数器 |
| 进程存活但端口不监听，health check 超时 | GatewayManager 卡在 `hermes gateway start` | 设置 `UPSTREAM=http://127.0.0.1:8642` 跳过 gateway 自启 |
| SPA 白屏（JS/CSS 404） | Vue SPA 用绝对路径 `/assets/...` `/api/...`，nginx 只代理了 `/webui/` | 添加 `location ~ ^/(assets\|api\|favicon\.ico\|socket\.io)` 额外代理到同一后端 |
| `.npmrc` 有 `prefix` 设置导致 nvm 报错 | nvm 与 npm global prefix 冲突 | `nvm use --delete-prefix v22.22.0 --silent` 临时绕过 |

## 进阶：同一域名多个服务

### 常见故障

| 坑点 | 原因 | 解决 |
|------|------|------|
| `status=216/GROUP` | user service NSS 查找失败 | 用 system-level service（装到 `/etc/systemd/system/`） |
| `Invalid Host header` | Host header 传了域名 | 改成 `127.0.0.1:9119` |
| `address already in use` | 重复启动 | 先 `hermes dashboard --stop` |
| 访问 401 | 密码错了 | `sudo htpasswd /etc/nginx/.htpasswd 用户名` 重设。如果带了正确密码还是 401，检查 Dashboard 服务是否在运行 |
| `wangsiji.site` 打不开 / 返回 401 或 502 | Dashboard 服务挂了 | `sudo systemctl status hermes-dashboard` 检查，`sudo systemctl start hermes-dashboard` 重启。注意：Dashboard 挂了时 nginx 仍会弹出 auth 弹窗，但输完密码还是 401 —— 这是 nginx 的 auth 先过但后端连不上。如果经常被 kill（如 OOM），检查 `journalctl -u hermes-dashboard --since "24 hours ago"` 看原因 |

### 改密码（交互式）

```bash
sudo htpasswd /etc/nginx/.htpasswd 用户名
```

### 改密码（非交互式，用于脚本或工具调用）

```bash
echo "新密码" | sudo htpasswd -i /etc/nginx/.htpasswd 用户名
```

注意：首次创建用 `-c`（会覆盖已有文件），后续添加或改密码**不要加 `-c`**。

### 想加另一个用户

```bash
sudo htpasswd /etc/nginx/.htpasswd 新用户名
```

注意：不要加 `-c` 参数，否则会覆盖已有的密码文件。

### 手动续期证书

```bash
sudo certbot renew
```
