# Hermes Web UI 自动更新导致 502（故障排查记录）

## 症状

每次 hermes-web-ui 检测到新版并自动更新后，访问 `https://wangsiji.site/webui/` 返回 502 Bad Gateway。systemd 显示 service 处于 `inactive (dead)` 状态。

## 日志证据

```log
[update] restart process exited before replacing server: code=1 signal=null
[shutdown] Received signal: SIGTERM
```

## 根因

hermes-web-ui 内置的自动更新流程：

1. 每 30 分钟检测一次新版本（日志中可见周期性的 `Update available: 0.6.3 → 0.6.5`）
2. 检测到新版后，下载并运行一个重启替换脚本
3. 重启脚本执行失败（`exit code=1`），无法启动新进程
4. 旧进程收到 SIGTERM 被系统杀掉
5. 由于 service 配置为 `Restart=on-failure`，而旧进程的 exit code 是 0（正常 SIGTERM），systemd 认为"正常退出"，**不会自动重启**
6. 服务永久挂了

## 推荐方案：禁用自动更新 + 手动升级

每次更新后都崩，说明内置更新脚本有 bug。直接关掉自动更新，改为可控的手动升级。

### 1. 禁用自动更新（立即生效）

在 systemd service 中添加环境变量：

```ini
Environment=HERMES_WEB_UI_DISABLE_UPDATE_CHECK=true
```

添加后执行 `systemctl --user daemon-reload && systemctl --user restart hermes-webui`。

这个 env var 是 hermes-web-ui 源码中实际读取的（`process.env.HERMES_WEB_UI_DISABLE_UPDATE_CHECK`）。**不是** `DISABLE_AUTO_UPDATE` 或其他拼写。

### 2. 手动升级步骤

方案 A（推荐）—— 用 nvm 的 npm 装，再复制到 NODE_PATH 目录：

```bash
# Step 1: 用 nvm 的 npm（系统 npm v20 需 root 权限，nvm 的 npm v24 可直接用户级装）
. ~/.nvm/nvm.sh && nvm use 24

# Step 2: 用 -g 装到 nvm 的全局目录
npm install -g hermes-web-ui@latest

# Step 3: 复制到 service 实际读取的路径
# ⚠️ service 的 NODE_PATH 指向 ~/.npm-global/lib/node_modules/，npm -g 装在 nvm 目录
NVM_PKG=$(npm root -g)/hermes-web-ui
LOCAL_PKG=~/.npm-global/lib/node_modules/hermes-web-ui
cp -r "$NVM_PKG/dist" "$LOCAL_PKG/"
cp "$NVM_PKG/package.json" "$LOCAL_PKG/package.json"

# Step 4: 检查版本
node -e "console.log(require('$LOCAL_PKG/package.json').version)"

# Step 5: 重启服务
systemctl --user restart hermes-webui
```

方案 B（备选）—— 用 --prefix 装到 ~/.npm-global：

```bash
. ~/.nvm/nvm.sh && nvm use 24
# --prefix 会把包装到 ~/.npm-global/node_modules/（flat 结构）
# 而 service 的 NODE_PATH 指向 ~/.npm-global/lib/node_modules/，
# 旧版在那里。装完后需要手动把 dist 和 package.json 复制过去。
npm install --prefix /home/wangsiji/.npm-global hermes-web-ui@latest

# 复制到 service 实际读取的路径
cp -r /home/wangsiji/.npm-global/node_modules/hermes-web-ui/dist \
      /home/wangsiji/.npm-global/lib/node_modules/hermes-web-ui/
cp /home/wangsiji/.npm-global/node_modules/hermes-web-ui/package.json \
   /home/wangsiji/.npm-global/lib/node_modules/hermes-web-ui/package.json

# 检查版本
node -e "console.log(require('/home/wangsiji/.npm-global/lib/node_modules/hermes-web-ui/package.json').version)"

# 重启服务
systemctl --user restart hermes-webui
```

### 临时恢复（服务已挂时）

```bash
systemctl --user start hermes-webui.service
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://wangsiji.site/webui/
```

### 备选方案：`Restart=always`（不推荐单独使用）

如果不想禁用自动更新，可以将 `Restart=on-failure` 改为 `Restart=always`。但更新脚本本身 crash（exit 1）的问题仍在，只是 systemd 会自动拉起来。更干净的做法是直接禁用自动更新，可控手动升级。

---

## 附录：daily-hermes-update cron 超时修复

另有每日凌晨 4 点的 cron 任务 `daily-hermes-update`（`no_agent: true`，脚本直接执行），超时后标记 `Script timed out after 120s`。

### 超时原因

原脚本调用 `hermes update`，内部执行完整流水线：

1. git fetch → git pull（快）
2. `pip install -e .[all]`（约 30–60s，编译 hermes-agent）
3. `npm install` in PROJECT_ROOT（慢，可 > 30s）
4. `npm install` in ui-tui/（慢）
5. web UI 构建（慢）

第 3–5 步在 VPS 上很容易超过 120s，导致 cron 杀死脚本。

### 修复方案

替换 cron 脚本内容，只做核心更新（git + pip），跳过所有 npm/webui 步骤：

```bash
cd /home/wangsiji/.hermes/hermes-agent

# 先查有没有新 commit，无则直接退出
git fetch origin --prune
COMMIT_COUNT=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
[ "$COMMIT_COUNT" = "0" ] && echo "已是最新" && exit 0

# 拉取 + 更新 python 依赖
git pull --ff-only origin main
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
source venv/bin/activate
uv pip install -e ".[all]" 2>&1 || python -m pip install -e ".[all]" 2>&1

echo "✅ 更新完成（仅核心，跳过 npm/webui）"
```

**关键改动：** 不调用 `hermes update`，而是手动拆解步骤。先 `git fetch` 检查 commit 数，无变更直接退出，避免每天跑一次 `uv pip install`。有变更才执行 `git pull + pip install`，跳过所有 npm 操作。

### 耗时对比

| 步骤 | 原 `hermes update` | 新脚本 |
|------|-------------------|--------|
| git fetch | ~5s | ~5s |
| git pull | ~1s | ~1s |
| pip install | ~40s | ~40s |
| npm install ×2 | ~60s+ | **跳过** |
| web UI build | ~30s+ | **跳过** |
| **总计** | **>120s ❌** | **~50s ✅** |

---

## 推理过程

1. 用户反馈更新后 502 → 检查 nginx 配置（200 OK on test）→ 排除 nginx
2. `curl http://127.0.0.1:8648/` → Connection refused → 后端挂了
3. `systemctl --user status hermes-webui` → `inactive (dead)`
4. `journalctl --user -u hermes-webui --no-pager -n 60` → 看到 `[update] restart process exited before replacing server: code=1 signal=null` 和随后的 `[shutdown] Received signal: SIGTERM`
5. 检查 service 配置 → `Restart=on-failure` → SIGTERM 导致 `exit code=0` → systemd 不重启
6. 搜索源码找关闭自动更新的 env var → `process.env.HERMES_WEB_UI_DISABLE_UPDATE_CHECK`
