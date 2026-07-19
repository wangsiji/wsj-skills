---
name: hermes-dashboard-webui
description: Hermes Dashboard + Web UI 部署配置：端口/反代/nginx/服务管理详细步骤
---

## 二、Hermes Dashboard + Web UI

### 2.1 Dashboard 部署

#### 启动

```bash
hermes dashboard                    # 启动
hermes dashboard --status           # 查看状态
hermes dashboard --stop             # 停止
curl http://127.0.0.1:9119/         # 验证
```

#### systemd 自启（system-level）

```bash
cat > ~/.local/bin/hermes-dashboard.sh << 'EOF'
#!/bin/bash
cd /home/wangsiji
source /home/wangsiji/.hermes/hermes-agent/venv/bin/activate
exec python -m hermes_cli.main dashboard
EOF
chmod +x ~/.local/bin/hermes-dashboard.sh

sudo tee /etc/systemd/system/hermes-dashboard.service << 'EOF'
[Unit]
Description=Hermes Agent Dashboard
After=network.target

[Service]
Type=simple
User=wangsiji
ExecStart=/home/wangsiji/.local/bin/hermes-dashboard.sh
WorkingDirectory=/home/wangsiji
Restart=always
RestartSec=10
SupplementaryGroups=

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now hermes-dashboard.service
```

> ⚠️ **为什么用 `Restart=always`**：`hermes update` 优雅关闭（exit 0），`on-failure` 不会拉起。
> ⚠️ **为什么用 system-level**：user-level 在某些 VPS 因 nsswitch.conf 含 `winbind` 导致 status=216/GROUP。

### 2.2 nginx 反代配置

```bash
# 设置密码
sudo htpasswd -c /etc/nginx/.htpasswd wangsiji

# nginx 配置
sudo tee /etc/nginx/sites-available/hermes-dashboard << 'EOF'
server {
    listen 443 ssl;
    server_name wangsiji.site;

    # SSL 由 certbot 自动管理

    # Dashboard — 官方面板
    location /hermes/ {
        auth_basic "Hermes Dashboard";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://127.0.0.1:9119/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host "127.0.0.1:9119";  # ⚠️ 必须！dashboard 校验 Host
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Web UI — 第三方全功能面板（自带登录）
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

    # Web UI SPA 前缀坑：JS/CSS/API 是绝对路径，需额外代理
    location ~ ^/(assets|api|favicon\\.ico|socket\\.io|upload|webhook|health|terminal) {
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

    # ⚠️ sites-enabled 是独立文件而非 symlink 时，编辑 sites-available 后必须手动复制
    # ls -l /etc/nginx/sites-enabled/  检查是否 symlink（→）
    # 如果是普通文件: sudo cp /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/
    # 建议改为 symlink: sudo ln -sf /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/

    # Feed 公开访问
    location /feed/ {
        auth_basic off;
        alias /var/www/info-feed/;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### HTTPS（免费证书）

```bash
sudo apt-get install -y nginx apache2-utils certbot python3-certbot-nginx
sudo certbot --nginx -d wangsiji.site --agree-tos --email 你的邮箱
```

### 2.3 Hermes Web UI（第三方）

```bash
# 安装
npm --prefix /home/wangsiji/.npm-global install hermes-web-ui

# 更新
npm --prefix /home/wangsiji/.npm-global update hermes-web-ui
```

> ⚠️ 安装路径是 `~/.npm-global/`，不是 `/usr/lib/node_modules/`。系统 npm 的 global prefix 默认是 `/usr`（需 sudo），但此 VPS 上已设 `prefix=~/.npm-global`。更新时用 `--prefix` 指定即可，不需要 `-g` 和 sudo。

Or using the daily cron script: `bash ~/.hermes/scripts/daily-hermes-update.sh`

⚠️ **需要 Node.js 22.5.0+**（`node:sqlite` 内置模块）：

```bash
# 检测
node -e "require('node:sqlite')" 2>&1 || echo "❌ 需要 Node 22.5.0+"
# 修复
nvm install 22
nvm use --delete-prefix 22 --silent
```

#### systemd 服务（user-level）

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/hermes-webui.service << 'EOF'
[Unit]
Description=Hermes Web UI
After=network.target hermes-gateway.service

[Service]
Type=simple
ExecStart=/usr/bin/node /home/wangsiji/.npm-global/lib/node_modules/hermes-web-ui/dist/server/index.js
Restart=always
RestartSec=5
Environment=PORT=8648
Environment=UPSTREAM=http://127.0.0.1:8642
Environment=NODE_PATH=/home/wangsiji/.npm-global/lib/node_modules
Environment=PATH=/home/wangsiji/.npm-global/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now hermes-webui.service
```

> ⚠️ `UPSTREAM` 必须设置，否则 Web UI 会尝试自启 gateway 导致冲突卡住。

### 2.4 验证清单（每次改完配置必跑）

```bash
# 1. 服务活着
systemctl status hermes-dashboard --no-pager | grep -q "active (running)" && echo "✅ Dashboard" || echo "❌ Dashboard"
systemctl --user status hermes-webui --no-pager | grep -q "active (running)" && echo "✅ Web UI" || echo "❌ Web UI"

# 2. 本地端口
curl -s -o /dev/null -w "✅ Dashboard: %{http_code}\n" http://127.0.0.1:9119/
curl -s -o /dev/null -w "✅ Web UI: %{http_code}\n" http://127.0.0.1:8648/

# 3. Gateway 正常
curl -s http://127.0.0.1:8642/health | grep -q '"status":"ok"' && echo "✅ Gateway" || echo "❌ Gateway"

# 4. 检查 sites-enabled 与 sites-available 是否同步
ls -l /etc/nginx/sites-enabled/ | grep hermes-dashboard
# 期望显示 →（symlink 箭头）若显示普通文件，cp 同步
```

### 2.5 常见故障

| 症状 | 根因 | 解决 |
|------|------|------|
| `Invalid Host header` | Host header 传了域名 | 改成 `127.0.0.1:9119` |
| 输完密码仍 401 | Dashboard 挂了 | `systemctl status hermes-dashboard` 检查 |
| Web UI 白屏 | SPA 路径前缀问题 | 加 `location ~ ^/(assets\\|api\\|...)` 代理 |
| Web UI 卡在初始化 | GatewayManager 冲突 | 设 `UPSTREAM=http://127.0.0.1:8642` |
| `ERR_UNKNOWN_BUILTIN_MODULE` | Node.js < 22.5.0 | nvm 安装 Node 22+ |
| `address already in use` | 旧进程 | `fuser -k 8648/tcp` |

### 2.6 Gateway 故障处理

**现象**：Telegram / 微信不响应，发送消息无回复。

**诊断步骤**：

```bash
# 1. 检查 gateway 进程状态
systemctl --user status hermes-gateway

# 2. 看最后几行 journal（含退出原因）
journalctl -u hermes-gateway --since "2 hours ago" --no-pager | tail -20

# 3. 检查是否 OOM 被杀（看 Mem peak 和 OOM 标记）
systemctl --user status hermes-gateway 2>&1 | grep -E "Mem peak|OOM|killed|signal"

# 4. 看内存情况
free -m

# 5. 看 gateway 日志里的连接状态
tail -30 ~/.hermes/logs/gateway.log
```

**OOM 特征**：`Main PID: ... (code=killed, signal=KILL)` + `Mem peak: 2.6G` + journal 中 `killed by the OOM killer`。

**恢复**：

```bash
systemctl --user start hermes-gateway
sleep 3
systemctl --user status hermes-gateway  # 确认 active (running)

# 验证通道
tail -10 ~/.hermes/logs/gateway.log
# 期望看到: ✓ telegram connected + ✓ weixin connected
```

**根因**：4GB VPS 上 gateway 进程峰值可达 2.6G+（运行长任务导致）。长任务（terminal timeout 循环等）是典型触发因素。

**预防措施**（如果频繁 OOM）：
- 调低 `agent.max_turns`（目前 90）
- 调低 `gateway_timeout`（目前 1800s）
- 给 systemd unit 加 `MemoryMax=2G` 限制（不过 OOM 时 gateway 进程会被系统杀掉而非优雅退出，建议先调参数）

> 详细：Dashboard 部署细节见 [references/nginx-config-template.md](references/nginx-config-template.md)
> Web UI 完整部署见 [references/hermes-web-ui-deployment.md](references/hermes-web-ui-deployment.md)

---

