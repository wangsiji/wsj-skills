# Hermes Web UI 部署记录（wangsiji.site）

## 架构

```
用户 → nginx :443 (/webui/) → hermes-web-ui :8648
                                     ↓ UPSTREAM=http://127.0.0.1:8642
                                Hermes Gateway (systemd user service)
```

## 关键发现 1：Node.js 版本要求（node:sqlite）

### 症状
服务启动失败，`journalctl --user -u hermes-webui.service` 报错：
```
Error [ERR_UNKNOWN_BUILTIN_MODULE]: No such built-in module: node:sqlite
```

### 根因
hermes-web-ui 使用了 Node.js 22.5.0+ 的内置模块 `node:sqlite`，但系统可能只有 Node.js v20（常见于 Debian/Ubuntu 稳定版）。

### 修复方案

如果装了 **nvm**：

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use --delete-prefix v22.22.0 --silent 2>/dev/null
node --version  # 确认 v22+
```

> 设置默认版本：`nvm alias default v24.16.0`，让新 shell 自动使用
> 查看可用版本：`nvm ls-remote`（确认有 v22+）
>
> ⚠️ 如果 `.npmrc` 中有 `prefix=/home/xxx/.npm-global`，会跟 nvm 冲突，报 `Your user's .npmrc file has a 'globalconfig' and/or a 'prefix' setting, which are incompatible with nvm`。解决方案：`nvm use --delete-prefix v22.22.0 --silent` 临时忽略。

更新 systemd service 中的 `ExecStart` 指向 nvm 的 Node：

```ini
ExecStart=/home/用户名/.nvm/versions/node/v22.22.0/bin/node /home/用户名/.npm-global/lib/node_modules/hermes-web-ui/dist/server/index.js
```

如果没有 nvm：

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# 或升级系统 Node（不推荐，Debian 稳定版通常太旧）
```

### 检测 Node 版本是否支持

```bash
node -e "require('node:sqlite')" 2>&1 || echo "❌ Node.js 版本太低，需要 22.5.0+"
```

## 关键发现 2：GatewayManager 卡死问题

### 症状
`hermes-web-ui start` 运行后进程存活但不监听端口，health check 超时。

### 根因
她的 GatewayManager（`dist/server/services/hermes/gateway-manager.js`）在启动时自动调用 `hermes gateway start`（systemd 方式）。如果 Gateway 已由 systemd 管理，这个调用要么超时（30s timeout），要么返回冲突状态，导致整个 bootstrap 流程卡在 `await gatewayManager.startAll()`。

### 修复方案
设置 `UPSTREAM=http://127.0.0.1:8642` 环境变量。这个配置在 `dist/server/config.js` 中定义：

```js
exports.config = {
    upstream: process.env.UPSTREAM || 'http://127.0.0.1:8642',
    // ...
};
```

设置了 UPSTREAM 后，GatewayManager 的 `detectStatus()` 仍会运行，但不会尝试启动新的 gateway 进程。它发现 gateway 已健康运行（通过 /health 端点检查）后就正常注册并继续启动 BFF server。

### 如何发现的
1. `curl http://127.0.0.1:8648/` → Connection refused（进程在但没监听）
2. `cat ~/.hermes-web-ui/server.log` → 停在 `"Starting gateway for profile 'default' (start mode, port: 8642)"`
3. 排查 `dist/server/index.js` → 看到 `await (0, gateway_bootstrap_1.initGatewayManager)()`
4. 排查 `dist/server/services/gateway-bootstrap.js` → 看到 `await gatewayManager.startAll()`
5. 排查 `dist/server/config.js` → 发现 `upstream` 配置项
6. 用 `UPSTREAM=http://127.0.0.1:8642` 启动，立刻成功

## 手动升级流程（重要）

### nvm npm prefix 坑

安装包时**必须用 `--prefix` 参数**，因为：
- systemd service 的 `ExecStart` 指向 `~/.npm-global/lib/node_modules/hermes-web-ui/`
- 但 nvm 管理的 npm 默认 prefix 是 `~/.nvm/versions/node/v24.16.0/`
- 不加 `--prefix` 时包会装到 nvm 目录，服务读不到新版

### 升级步骤

```bash
# 1. 用 nvm 的 npm（Node 24+）
. ~/.nvm/nvm.sh && nvm use 24

# 2. 安装最新版到 ~/.npm-global
npm install --prefix /home/wangsiji/.npm-global hermes-web-ui@latest

# 3. 验证版本
node -e "console.log(require('/home/wangsiji/.npm-global/lib/node_modules/hermes-web-ui/package.json').version)"

# 4. 重启服务
systemctl --user reset-failed hermes-webui.service   # 避免重启计数器耗尽
systemctl --user restart hermes-webui.service

# 5. 验证
sleep 4
systemctl --user is-active hermes-webui && curl -s -o /dev/null -w "HTTP %{http_code}\n" https://wangsiji.site/webui/
```

### 禁用自动更新

在 `~/.config/systemd/user/hermes-webui.service` 的 `[Service]` 段添加：

```ini
Environment=HERMES_WEB_UI_DISABLE_UPDATE_CHECK=true
```

然后 `systemctl --user daemon-reload && systemctl --user restart hermes-webui`。

这个 env var 是源码中实际检查的（`process.env.HERMES_WEB_UI_DISABLE_UPDATE_CHECK`），不是 `DISABLE_AUTO_UPDATE`。

User-level service（非 system-level），因为：
- hermes-web-ui 是 Node.js 应用，不需要 root
- 不会跟 hermes-dashboard（system-level systemd service）冲突
- ~/.config/systemd/user/ 管理起来更灵活

## 关键发现 3：EADDRINUSE 与 systemd 重启计数器

### 症状
service 启动后立即退出，日志显示 `FATAL: Failed to start Hermes Web UI` + `Error: listen EADDRINUSE: address already in use 0.0.0.0:8648`。systemd 持续 auto-restart，最终重启计数器耗尽，service 永远失败。

### 根因
之前通过 `hermes-web-ui start` 或手动启动的进程仍占用 8648 端口。systemd 启动新实例时端口已占用，启动失败 → auto-restart → 还是端口被占 → 失败循环。

### 修复

```bash
# 1. 找占用进程
ss -tlnp | grep 8648

# 2. 杀掉
kill -9 <PID>

# 3. 清除 systemd 重启计数器（重要！不 reset 会继续快速失败）
systemctl --user reset-failed hermes-webui.service

# 4. 启动
systemctl --user start hermes-webui.service
```

> ⚠️ 如果 `fuser -k 8648/tcp` 不生效（The command might fail on some systems），改用 `kill -9 PID`。

### 预防
每次 `hermes-web-ui start` 前确认没有残留进程：
```bash
fuser 8648/tcp 2>/dev/null || echo "Port 8648 free"
```

## 关键发现 4：SPA 路径前缀白屏问题

### 症状
`https://域名/webui/` 返回 HTML（200）但页面白屏。浏览器 DevTools Network 面板显示 JS/CSS 请求（`/assets/js/...`、`/assets/css/...`）返回 404 或无法加载。

### 根因
Vue SPA 打包时资源路径是硬编码的绝对路径（如 `<script src="/assets/js/index-xxx.js">`），不受 nginx 的路径前缀约束。当 SPA 部署在 `/webui/` 下时：

1. 用户访问 `/webui/` → nginx 去掉 `/webui` 前缀后转发到后端 → 后端返回 HTML
2. HTML 中 `<script src="/assets/js/index-xxx.js">` → 浏览器解析为 `https://域名/assets/js/index-xxx.js`（不是 `/webui/assets/...`）
3. nginx 没有处理 `/assets/...` 的请求 → 404 → JS 不执行 → 白屏

### 修复方案

在 nginx 中额外代理这些根路径到同一个后端：

```nginx
# Web UI SPA HTML（必须在 /webui/ 下）
location /webui/ {
    auth_basic off;
    proxy_pass http://127.0.0.1:8648/;
    ...
}

# 前端资源 + API + WebSocket — 用绝对路径请求，不受 /webui/ 保护
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

注意 regex location (`~ ^/(assets|...)`) 的 `proxy_pass` 末尾**不能加 `/`**（跟精确 location 的写法不同），否则路径会被双重处理。

### 此问题的通用性

这不是 hermes-web-ui 的 bug，而是**所有未配置 base URL 的 SPA 部署在 nginx 路径前缀下的通病**。其他例子：Vite/Webpack 默认 build 产出的 SPA、React/Vue/Angular 的默认配置。解决方案有：
1. **nginx 额外 location**（本文采用）—— 简单，不修改前端代码
2. **前端配置 base URL**（Vite 的 `base` 配置、Vue Router 的 `base`）—— 更干净但需要修改 build 配置
3. **子域名** —— 最干净但要多一个 DNS 记录

### 如何排查

浏览器 F12 → Network 面板：
- 看 HTML 请求 → 200 ✅
- 看 JS/CSS 请求 → 如果 404 ❌ → 就是路径前缀问题
- Console 面板 → 如果有 `Failed to load module script` 或 `Unexpected token '<'`（说明返回了 HTML 而不是 JS） → 同样问题

```bash
# 命令行验证
curl -s -o /dev/null -w "%{http_code}" https://域名/assets/js/index-*.js
# 返回 200 ✅ 或 404 ❌
```

### 关于 nvm alias default

安装好 Node 22+ 后用 `nvm alias default <版本号>` 设置默认版本，否则新 shell 启动时仍会用系统自带的旧版 Node。这个对 systemd service 没影响（ExecStart 指向绝对路径），但手动调试时有用。当前系统已设为 `v24.16.0`：

## 关键发现 5：`.npmrc prefix` 与 nvm 冲突

### 症状
nvm 命令报错：
```
Your user's .npmrc file (${HOME}/.npmrc)
has a `globalconfig` and/or a `prefix` setting, which are incompatible with nvm.
```

### 根因
`~/.npmrc` 中有 `prefix=/home/xxx/.npm-global` 设置。nvm 管理自己的 Node 版本和 global prefix，与固定 prefix 冲突。

### 修复
```bash
# 临时绕过（不修改 .npmrc）
nvm use --delete-prefix v22.22.0 --silent

# 或移除 .npmrc 中的 prefix 行（让 nvm 管理 global 安装位置）
# 注意：移除后之前安装在 ~/.npm-global 的包需要通过 npm link 或重新安装才能用
sed -i '/^prefix=/d' ~/.npmrc
```

### 设置 nvm 默认版本

安装好目标版本后设为默认，让新终端自动使用：
```bash
nvm alias default v24.16.0
```
> systemd service 的 `ExecStart` 指向绝对路径，不受 nvm default 影响。但设置默认版本对手动调试有用。

## 关键发现 6：Web UI 自带鉴权 → 去掉 nginx auth_basic

第一次部署时对 `/webui/` 加了 `auth_basic`，用户反馈 401。原因是 Web UI 自带登录页面，nginx Basic Auth 成了多余的认证层。

**判断原则：**
- 后端无鉴权（如官方 Dashboard）→ 用 nginx auth_basic
- 后端自带鉴权（登录页/token）→ `auth_basic off`
- 不要双重认证

## nginx 配置要点

与 Dashboard 的区别：

| 特性 | Dashboard (/hermes/) | Web UI (/webui/) |
|------|---------------------|------------------|
| Host header | `127.0.0.1:9119`（校验） | `$host`（不校验） |
| X-Forwarded-Prefix | `/hermes`（必需） | 不需要 |
| 认证 | auth_basic + 内部 token | auth_basic + 内部 token/账号 |
| 后端 | Python | Node.js |
| 内存 | ~200MB | ~63MB |
