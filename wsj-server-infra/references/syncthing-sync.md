---
name: syncthing-sync
description: Syncthing 文件同步配置：设备配对/忽略规则/冲突处理/nginx 暴露
---

## 三、Syncthing 文件同步

### 3.1 安装与自启

```bash
# 安装（最新版）
cd /tmp
LATEST=$(curl -s https://api.github.com/repos/syncthing/syncthing/releases/latest | grep "browser_download_url.*linux-amd64" | head -1 | cut -d'"' -f4)
curl -sLO "$LATEST"
tar xzf syncthing-linux-amd64-*.tar.gz
sudo cp syncthing-linux-amd64-*/syncthing /usr/local/bin/
sudo mkdir -p /var/syncthing
sudo chown $USER:$USER /var/syncthing
/usr/local/bin/syncthing --version

# systemd 服务（user-level）
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/syncthing.service << 'EOF'
[Unit]
Description=Syncthing

[Service]
ExecStart=/usr/local/bin/syncthing serve --no-browser --no-restart --gui-address=127.0.0.1:8384 --home=/var/syncthing
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now syncthing

# 确保 VPS 重启后自启
loginctl enable-linger wangsiji
```

#### ⚠️ 安装后必须：禁用自动升级

Syncthing 默认每 12 小时尝试自动升级。如果 `/usr/local/bin/syncthing` 对当前用户不可写（通常需要 sudo），升级会失败并报 `permission denied`，残留临时文件污染进程状态，导致连接断断续续。

```bash
# 将 autoUpgradeIntervalH 设为 0
sed -i 's|<autoUpgradeIntervalH>[0-9]*</autoUpgradeIntervalH>|<autoUpgradeIntervalH>0</autoUpgradeIntervalH>|' /var/syncthing/config.xml
grep autoUpgrade /var/syncthing/config.xml  # 确认显示 0
systemctl --user restart syncthing          # 重启生效
```

#### ⚠️ 2 个进程是正常的

Syncthing v2.1.1+ 启动两个进程：主进程（`Ssl`）和工作进程（`SNl`，低优先级做 CPU 密集型工作）。这是正常行为，不是冲突。如果出现 3+ 个进程才是多进程冲突——`pkill -9 -f syncthing` 杀干净后只通过 systemd 启动即可。

### 3.2 配置

**VPS 信息**：
- 设备 ID：`XTMLFNH-LYUQY2I-XERNZRV-MOYENQA-PTTAM5X-O56DP5F-WSHVBWF-5WMC2AA`
- 同步文件夹：`/home/wangsiji/projects/wsj-second-brain`（文件夹 ID: `obsidian-vault`）

**添加设备**（优先用 REST API，比 XML 编辑更安全）：

```bash
# 获取 API key
grep '<apikey>' /var/syncthing/config.xml

# API 方式添加设备（无需重启）
# GET 当前配置 → 修改 JSON → POST 回写
curl -s -H "X-API-Key: YOUR_API_KEY" http://127.0.0.1:8384/rest/system/config > /tmp/syncthing_config.json

# 编辑设备列表和文件夹设备列表
python3 -c "
import json
cfg = json.load(open('/tmp/syncthing_config.json'))
# 添加新设备（替换 DEVICE_ID 和 name）
new_dev = {
    'deviceID': 'DEVICE_ID',
    'name': 'iPhone',
    'addresses': ['relay://global'],
    'compression': 'metadata',
    'introducer': False,
    'autoAcceptFolders': True,
    'paused': False
}
cfg['devices'].append(new_dev)
# 同时把设备加入文件夹
for f in cfg['folders']:
    f['devices'].append({'deviceID': 'DEVICE_ID', 'introducedBy': ''})
json.dump(cfg, open('/tmp/syncthing_config.json', 'w'), indent=2)
"

# POST 回写
curl -s -X POST -H "X-API-Key: YOUR_API_KEY" -H "Content-Type: application/json" \
  -d @/tmp/syncthing_config.json http://127.0.0.1:8384/rest/system/config

# 重载生效
curl -s -X POST -H "X-API-Key: YOUR_API_KEY" http://127.0.0.1:8384/rest/system/restart
```

> 为什么 REST API 优于直接编辑 XML：① 不会手误破坏 XML 结构导致 Syncthing 崩溃；② 不需要停止/重启服务做配置变更；③ 文件夹和设备关联一次完成。如 API 返回 `Method Not Allowed`，用 `POST` 而非 `PUT`。

**移除设备**（同理）：

```python
# 从 GET 的 config 中：
cfg['devices'] = [d for d in cfg['devices'] if d['deviceID'] != '要删除的ID']
for f in cfg['folders']:
    f['devices'] = [d for d in f['devices'] if d['deviceID'] != '要删除的ID']
# 然后 POST 回写 + restart
```

**端口**：
- `8384` — Web GUI（仅本地，SSH 隧道访问）
- `22000` — 数据传输
- `21027` — UDP 局域网发现

### 3.3 忽略模式（.stignore）

不同步同步文件夹内的某些子目录或文件，在同步文件夹根目录创建 `.stignore` 文件：

```
// 注释行用 //
// 排除目录
.obsidian/
node_modules/
_archive/

// 排除文件类型
*.log
*.tmp
.DS_Store

// 排除+取反（同步某子项的同时排除其他）
private/**/*
!private/important.md
```

- 支持 glob 通配符（`*`, `**`, `?`）
- 文件改完 **自动生效**，不需要重启 Syncthing
- 同文件夹内所有设备共享同一套忽略规则
- 删除 `.stignore` 文件即可恢复全量同步
- 选择性同步（Selective Sync）：Syncthing GUI 中可对每台设备单独选择不同步哪些子目录
- 常见用途：排除 `.obsidian/`（但用户最终选择全量同步，认为工具配置也是知识资产）

### 3.4 日常验证

```bash
# 进程
ps aux | grep syncthing | grep -v grep
# 端口
ss -tlnp | grep -E '8384|22000'
# API
curl -s http://127.0.0.1:8384/rest/system/ping -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
# 同步状态
curl -s "http://127.0.0.1:8384/rest/db/status?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
```

### 3.4 触发扫描（新建目录后必做）

```bash
curl -X POST "http://127.0.0.1:8384/rest/db/scan?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
```

### 3.5 常见故障

| 症状 | 根因 | 解决 |
|------|------|------|
| Remote Devices Disconnected | 进程挂了 | `ps aux | grep syncthing` → 启动 |
| 连接断断续续（反复 Lost/Established） | 版本不匹配 或 自动升级失败 或 iOS 后台杀进程 | 升级到一致版本 + 禁用自动升级；iPhone 正常现象 |
| State: error, insufficient space | 磁盘 < 1% | `pip3 cache purge; journalctl --vacuum-time=7d` |
| GUI 无响应 / curl exit 7 | 多进程抢端口 | `pkill -9 -f syncthing` 杀干净再启 |
| 文件夹 ID 不匹配 | iPhone 自动生成带空格 ID | 手动设稳定 ID `obsidian-vault` |
| GUI 暴露公网 | `--gui-address` flag 覆盖 config.xml | 改成 `127.0.0.1`，必须与 config.xml 一致 |
| `Lost device connection ... (remote): closing` | 对方设备主动断开（iPhone 锁屏、Mac 休眠） | 正常行为，对方上线后会自动重连 |
| Automatic upgrade failed + 连接异常 | 自动升级尝试写 `/usr/local/bin/syncthing` 权限不足 | 禁用自动升级（设 `autoUpgradeIntervalH=0`）后重启 |

### 3.6 iPhone 同步方案

iPhone 上 Obsidian vault 在 iCloud 沙箱中，**Syncthing 无法直接访问**。但 iOS 端仍然可以使用 Syncthing 应用（SushiTrain / Mobius Sync）同步非 iCloud 目录的文件夹。

#### iOS 官方态度

Syncthing 官方 FAQ 明确说明：**"There are no plans by the current Syncthing team to officially support iOS."** iOS 限制太严格，不可能像桌面端那样运行。现有第三方 App：

| 方案 | 类型 | 说明 |
|------|------|------|
| [SushiTrain](https://github.com/pixelspark/sushitrain) | 免费开源 | 原生 UI，选择性同步，大部分功能可用 |
| [Mobius Sync](https://www.mobiussync.com) | 商业付费 | 原版 Syncthing UI 完整功能 |

#### iOS 后台保活

iOS **没有完美的后台保活方案**。Apple 系统级限制：锁屏后几分钟到十几分钟内后台进程会被杀。这不是 App 问题。

最大化存活时间的设置：

- **必做**：设置 → 通用 → 后台 App 刷新 → 打开 Syncthing 应用
- **关闭低电量模式**（低电量模式直接砍后台）
- **打开通知权限**（有通知的 App iOS 会给更多后台时间）
- **用完别上滑杀掉 App**，留在 App Switcher 里即可（滑掉 = 进程立即被杀）

本质认知：iOS Syncthing 是**按需同步工具**，不是 24h 在线守护进程。需要在同步时打开 App，等几秒连接完成再关闭。

如果 Obsidian vault 放在 iCloud 内，Syncthing 无法访问该目录（iOS 沙箱限制）。替代方案用 WebDAV 直连 VPS：

```bash
pip install wsgidav cheroot
wsgidav --host=0.0.0.0 --port=8385 \
  --root=/home/wangsiji/projects/wsj-second-brain \
  --auth=anonymous
```

iPhone Obsidian → 设置 → 保险库 → 远程存储 → 添加 WebDAV：
- 服务器：`http://VPS_IP:8385`
- 用户名/密码：留空

> 注意：当前匿名访问，建议防火墙限制 iPhone IP。

### 3.7 磁盘空间清理

```bash
pip3 cache purge                    # pip 缓存（最大头）
sudo journalctl --vacuum-time=7d    # 日志
sudo apt-get clean                   # apt 缓存
npm cache clean --force              # npm 缓存
rm -rf ~/.config/google-chrome/Crash\ Reports/*.dmp
```

---

