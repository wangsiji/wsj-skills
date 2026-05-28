---
name: syncthing-setup
description: Syncthing 点对点文件同步 — VPS 搭建、多设备配置、端口被封解决方案
category: devops
triggers:
  - "Syncthing"
  - "跨设备同步"
  - "Obsidian 同步"
  - "文件同步到 VPS"
  - "Syncthing 断开连接"
  - "设备 ID"
---

# Syncthing 多设备文件同步

## 场景
在 Mac/iPhone/VPS 之间同步 Obsidian 笔记库（或其他文件夹），任意一端改动，其他端自动同步。
- Mac ↔ iPhone：通过 iCloud 原生同步，不需要 Syncthing 介入
- VPS：通过 Syncthing 增量同步 Mac 本地文件

## VPS 端安装与配置

### 安装（Linux amd64）
```bash
# 下载 Syncthing
cd /tmp
curl -LO https://github.com/syncthing/syncthing/releases/download/v2.0.16/syncthing-linux-amd64-v2.0.16.tar.gz
tar xzf syncthing-linux-amd64-v2.0.16.tar.gz
sudo cp syncthing-linux-amd64-v2.0.16/syncthing /usr/local/bin/
sudo mkdir -p /var/syncthing
sudo chown $USER:$USER /var/syncthing

# 配置自启动（systemd）
cat > ~/.config/systemd/user/syncthing.service << 'EOF'
[Unit]
Description=Syncthing

[Service]
ExecStart=/usr/local/bin/syncthing serve --home=/var/syncthing --no-browser --gui-address=0.0.0.0:8384
Restart=always
User=wangsiji

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now syncthing
```

### systemd 服务文件（正确版本）

```ini
# ~/.config/systemd/user/syncthing.service
[Unit]
Description=Syncthing

[Service]
ExecStart=/usr/local/bin/syncthing serve --no-browser --no-restart --gui-address=127.0.0.1:8384 --home=/var/syncthing
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**注意**：`--gui-address` 必须与 config.xml 中 `<gui><address>` 的值一致。两者都是 `127.0.0.1:8384` 则只监听本地（安全）；两者都是 `0.0.0.0:8384` 则暴露公网无认证。优先使用 `127.0.0.1`。GUI 不需要对外暴露，远程管理走 SSH 隧道：
```bash
# 远程访问 VPS Syncthing GUI（本地端口转发）
ssh -L 18384:127.0.0.1:8384 root@your-vps-ip
# 然后本地浏览器打开 http://localhost:18384
```

```bash
# 启用并启动
systemctl --user daemon-reload
systemctl --user enable syncthing
systemctl --user start syncthing

# 验证
systemctl --user status syncthing
# 确认：Active: active (running)
```

**确保 VPS 重启后也能自启**（必须先开启 lingering）：
```bash
loginctl show-user wangsiji | grep Linger
# 如果 Linger=no，执行：
sudo loginctl enable-linger wangsiji
```

### 手动启动（不用 systemd 时）

**正确方式**：用 terminal 的 `background=true` 参数启动，不要用 nohup：
```bash
# 杀掉旧进程
pkill -9 -f syncthing; sleep 1

# 用 background=true 启动（禁止 nohup/disown/setsid）
syncthing serve --no-browser --no-restart --gui-address=0.0.0.0:8384 --home=/var/syncthing
```

**验证**：
```bash
sleep 3
curl -s http://127.0.0.1:8384/rest/system/ping
# 期望：{"ping":"pong"} 或 {"ping":"pong"} 加 CSRF Error（正常）
ss -tlnp | grep -E '8384|22000'
# 确认两个端口都在 LISTEN
```

### 端口
- `8384`（TCP）：Web GUI
- `22000`（TCP+QUIC）：Syncthing 数据传输
- `21027`（UDP）：本地发现（局域网内设备发现）

## 已知问题：VPS 端口被封

**症状**：设备状态显示「已断开连接」，VPS 上 Syncthing 进程正常但 Mac 无法连接。

**原因**：很多 VPS 服务商（RackNerd、Vultr 等）默认屏蔽入站 TCP/UDP 22000 端口。

**解决方案**：开启 Global Relay 中继（不依赖直连端口）

1. VPS Web UI → 设置 → 连接 → 勾选「启用全球发现」「启用全球中继服务器」
2. 保存后设备通过公共中继服务器（`relays.syncthing.net`）建立连接，不依赖直连端口

## 手动配置设备（最可靠方法：直接编辑 config.xml）

**坑**：Syncthing v2.0 REST API 端点格式不稳定，`/rest/devices` 经常返回 405/404。直接编辑 config.xml 是最可靠的方式。

### 添加设备
```python
import re

with open('/var/syncthing/config.xml', 'r') as f:
    content = f.read()

device_xml = '''<device id="MAC的设备ID" name="Mac" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
        <address>relay://global</address>
        <paused>false</paused>
        <autoAcceptFolders>true</autoAcceptFolders>
        <maxSendKbps>0</maxSendKbps>
        <maxRecvKbps>0</maxRecvKbps>
    </device>'''

# 在 VPS 自身设备条目之后插入
vps_id = "XTMLFNH-LYUQY2I-XERNZRV-MOYENQA-PTTAM5X-O56DP5F-WSHVBWF-5WMC2AA"  # 替换为实际 VPS 设备 ID
pattern = r'(<device id="' + vps_id + r'"[^>]*>.*?</device>)'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + '\n    ' + device_xml + content[insert_pos:]
    with open('/var/syncthing/config.xml', 'w') as f:
        f.write(new_content)
    print('Device added')
```

### 添加/修改文件夹
```python
content = content.replace('id="dm4tf-trk9a"', 'id="obsidian-vault"')  # 清理旧自动生成的 ID
content = content.replace('path="dm4tf-trk9a"', 'path="/home/wangsiji/syncthing/Obsidian"')
```

### 重启 Syncthing
```bash
# 杀掉旧进程
kill $(ps aux | grep 'syncthing serve' | grep -v grep | awk '{print $2}')
sleep 2

# 启动（用 background=true，不使用 nohup）
/usr/local/bin/syncthing serve --home=/var/syncthing --no-browser --gui-address=0.0.0.0:8384

# 验证
curl -s http://127.0.0.1:8384/rest/system/ping
# 期望：{"ping":"pong"}
```

### ⚠️ 坑：磁盘空间不足导致 Syncthing 报 error 状态

**症状**：VPS 端新文件不同步到手机/其他设备，Web UI 显示文件夹状态为 `error`。

**API 检查命令**：
```bash
curl -s "http://127.0.0.1:8384/rest/db/status?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('State:', d['state'])
print('Error:', d.get('error', '-'))
print('Need:', d['needTotalItems'])
"
```

**关键错误信息**：
```
insufficient space on disk for database (/var/syncthing/index-v2): current X.XX % < required 1 %
```

**原因**：磁盘使用率超过 99%，Syncthing 数据库需要至少 1% 空闲空间才能写索引。

**排查**：
```bash
df -h /
# 找空间大户
sudo du -sh /var/log/*/ 2>/dev/null | sort -rh | head -5
du -sh /home/wangsiji/.cache/pip/ 2>/dev/null
```

**清理命令**（按收益排序）：
```bash
# pip 缓存（常见最大头，可到 10G+）
pip3 cache purge

# systemd journal 日志（保留最近 7 天）
sudo journalctl --vacuum-time=7d

# apt 缓存
sudo apt-get clean

# npm 缓存
npm cache clean --force

# Chrome 崩溃报告
rm -rf ~/.config/google-chrome/Crash\ Reports/*.dmp ~/.config/chrome-cdp/Crash\ Reports/*.dmp
```

**修复后**：重启 Syncthing 并触发全量扫描：
```bash
pkill -9 -f syncthing; sleep 1
syncthing serve --no-browser --no-restart --gui-address=127.0.0.1:8384 --home=/var/syncthing
sleep 3
curl -X POST "http://127.0.0.1:8384/rest/db/scan?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
```

**新增文件后主动推送**：在 VPS 上用 Web Clipper 剪藏等操作新增文件后，触发一次扫描确保移动端收到：
```bash
curl -X POST "http://127.0.0.1:8384/rest/db/scan?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
```

## Syncthing 故障排查第一检查项

| 症状 | 原因 | 解决 |
|------|------|------|
| Remote Devices 显示 Disconnected | 进程挂了 | `ps aux \| grep syncthing`，启动 |
| State: error, "insufficient space on disk for database" | 磁盘空间 < 1% | `df -h /` → 清理: `apt-get clean; pip3 cache purge; journalctl --vacuum-time=7d` |
| GUI 无响应 / curl exit code 7 | 多进程抢端口 | `pkill -9 -f syncthing` 杀干净再启动 |

**症状**：Remote Devices 显示 Disconnected，VPS 上 Syncthing Web UI 打不开或 API 无响应。

**第一步永远是检查进程是否在跑**：
```bash
ps aux | grep syncthing | grep -v grep
curl -s http://127.0.0.1:8384/rest/system/ping
```
如果进程不存在（没有输出），先启动。不要先查日志、配置、网络——先确认进程活着。

### ⚠️ 坑：多进程冲突（今天刚遇到）

**症状**：ps 显示多个 syncthing 进程，端口被占，API 完全无响应（curl 报 exit code 7），设备全部 Disconnected。

**原因**：之前用 `nohup ... &` 在后台启动，同时 systemd 也在启动，3个进程抢端口。

**排查**：
```bash
ps aux | grep syncthing | grep -v grep
# 出现 2+ 个 syncthing 进程就是冲突
```

**修复**：
```bash
# 一次性杀干净（用 -9 + -f 双重保险）
pkill -9 -f syncthing; sleep 1
# 确认杀干净
ps aux | grep syncthing | grep -v grep  # 应该无输出
```

**正确启动方式**：用 systemd 管理，不要混用 nohup/后台 shell：
```bash
systemctl --user start syncthing
systemctl --user status syncthing  # 确认 active (running)
```

### ⚠️ 坑：GUI 监听地址导致外网无法访问 / 过度暴露

**场景一（今天刚遇到）**：config.xml 改成了 127.0.0.1:8384，但 systemd ExecStart 里是 `--gui-address=0.0.0.0:8384`，命令行 flag **覆盖** config.xml，GUI 仍然暴露公网无认证。

**核心规则**：命令行 `--gui-address` flag 优先级高于 config.xml。无论 config.xml 里怎么配，只要 ExecStart 里指定了 flag，就以 flag 为准。

**场景二**：用户不需要 GUI 管理，只需要同步功能。8384 GUI 暴露公网是安全风险。

**排查**：
```bash
ss -tlnp | grep 8384
# 0.0.0.0:8384 = 公网可访问（危险）
# 127.0.0.1:8384 = 仅本地（安全）
```

**修复（改为本地监听）**：
```bash
# 1. 改 config.xml
sed -i 's|<address>0.0.0.0:8384</address>|<address>127.0.0.1:8384</address>|' /var/syncthing/config.xml

# 2. 改 systemd service ExecStart（必须与 config.xml 一致）
sed -i 's|--gui-address=0.0.0.0:8384|--gui-address=127.0.0.1:8384|' ~/.config/systemd/user/syncthing.service

# 3. 重载并重启
systemctl --user daemon-reload
systemctl --user restart syncthing

# 4. 验证
ss -tlnp | grep 8384  # 应该显示 127.0.0.1:8384
```

**远程管理 GUI**：VPS 上 Syncthing GUI 改为本地监听后，远程管理走 SSH 隧道：
```bash
ssh -L 18384:127.0.0.1:8384 root@your-vps-ip
# 本地浏览器打开 http://localhost:18384
```

### 重启 Syncthing（正确方式）

**不要用 nohup/background 混用**，会导致进程跑到 shell wrapper 里被误判。用 terminal 的 `background=true` 参数：

```bash
# 杀掉旧进程
kill $(ps aux | grep 'syncthing serve' | grep -v grep | awk '{print $2}')

# 启动（用 background=true）
/usr/local/bin/syncthing serve --home=/var/syncthing --no-browser --gui-address=0.0.0.0:8384
```

**验证**：
```bash
sleep 3
curl -s http://127.0.0.1:8384/rest/system/ping
# 期望：{"ping":"pong"}
```

---

## 坑：文件夹 ID 必须预先匹配

**症状**：`Failed to auto-accept folder due to path conflict`

**原因**：Mac/iPhone 发送的文件夹邀请带有自动生成的 ID，与 VPS 上配置的不一致。最常见情况是 iPhone Syncthing 自动生成的文件夹 ID 带有空格（如 `   obsidian-vault`），导致 ID 匹配失败。

**排查方法**：
```bash
# 查看 VPS config.xml 中实际配置的文件夹 ID
grep '<folder ' /var/syncthing/config.xml | head -5
# 查看 iPhone 日志中的文件夹 ID
# VPS 日志中会出现：Unexpected folder ID in ClusterConfig
```

**解决方案**：
1. iPhone 上手动修改文件夹 ID：Syncthing → 文件夹 → 编辑 → 文件夹 ID 手动填写为 `obsidian-vault`（不能有空格）
2. 如果已有重复的文件夹配置，先删除再重建
3. 双方都改完后，重启两端 Syncthing

**操作顺序**：
1. **VPS 先配好**文件夹（ID 固定为 `obsidian-vault`，路径指向实际 vault 目录）
2. iPhone 添加文件夹时手动填相同 ID `obsidian-vault`，不要用自动生成的
3. 两边 ID 一致后，等待 relay 握手（10-30 秒）
4. 日志出现 `Established secure connection` + `Ready to synchronize` 即成功

**推荐操作顺序**：
1. Mac 添加 VPS 设备（地址填 `relay://global`）
2. Mac 添加文件夹，ID 填稳定名称如 `obsidian-vault`，路径选 Obsidian 库
3. 同时 VPS 上也用相同 ID 创建文件夹
**修复**：Mac 上点击设备行 → Address 改为 `relay://global`，保存。
- 同时确认 Mac Settings → Connection 里 Global Discovery 和 Global Relay 都已启用
- Relay Server Address 填：`relays.syncthing.net`
- 等待 10-30 秒，状态应变为 Connected

### 坑：VPS config.xml 中重复的文件夹条目

**症状**：Web UI 显示两个 `obsidian-vault` 文件夹，设备状态混乱，同步时断时续。

**原因**：iPhone 自动接受了两次文件夹邀请，在 VPS config.xml 中写入了两个不同的 `<folder>` 条目（一个是带空格的 ID，一个是正常 ID）。这会导致 Syncthing 行为不确定。

**修复**：
```bash
# 查看重复条目
grep -n '<folder ' /var/syncthing/config.xml

# 编辑器打开，手动删除带空格 ID 的重复条目
# 只保留 id="obsidian-vault" 且 path=/home/wangsiji/syncthing/Obsidian/wsj-second-brain 的那个
```

**预防**：iPhone 添加文件夹时手动指定稳定 ID，不要用自动生成的。

### 坑：文件夹路径必须完全一致

### VPS端（已知设备ID和路径）
- 设备ID：`XTMLFNH-LYUQY2I-XERNZRV-MOYENQA-PTTAM5X-O56DP5F-WSHVBWF-5WMC2AA`
- GUI端口：`8384`
- 数据端口：`22000`
- 文件夹路径：`/home/wangsiji/syncthing/Obsidian/wsj-second-brain`
- Syncthing备份目录：`/home/wangsiji/syncthing/Obsidian/wsj-second-brain`（VPS本地备份）
- WebDAV服务器端口：`8385`（用于iPhone Obsidian直连VPS，作为Syncthing的备选方案）

### Mac 端
1. 安装：`brew install syncthing`
2. 启动：`syncthing serve` → Web UI：`http://localhost:8384`
3. 操作菜单 → 添加远程设备 → 输入 VPS 设备 ID → 保存
4. 添加文件夹 → 路径选 Obsidian 库路径 → ID 手动填 `obsidian-vault` → 分享给 VPS

### iPhone 端
1. App Store 下载 **Syncthing** 或 **Syncthing Lite**
2. 同样添加 VPS 设备 → 分享同一文件夹

## 验证

**快速检查脚本**（推荐）：
```bash
bash ~/.hermes/skills/devops/syncthing-setup/scripts/syncthing-status.sh
```

**手动验证**：
```bash
# 检查 Syncthing 进程
ps aux | grep syncthing | grep -v grep

# 检查端口
ss -tlnp | grep -E '8384|22000'

# 测试 API
curl http://127.0.0.1:8384/rest/system/ping \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
# 期望：{"ping":"pong"}

# 查看连接状态（从日志）
# 搜索 "Established secure connection" 和 "Joined relay"
```

## 坑：新建子目录不同步（fs watcher 不检测新目录）

**症状**：在同步目录下新建子文件夹（如 `秋秋很开心/`），Syncthing Web UI 不出现该文件夹，iPhone 收不到。

**原因**：Syncthing 的 fs watcher 只检测已存在目录下的文件变化，不会自动发现新目录。必须手动触发扫描。

**解决**：
```bash
curl -X POST "http://127.0.0.1:8384/rest/db/scan?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"

# 验证同步状态
curl -s -X GET "http://127.0.0.1:8384/rest/db/status?folder=obsidian-vault" \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f\"Global:{d.get('globalFiles',0)} Local:{d.get('localFiles',0)} Need:{d.get('needFiles',0)} state:{d.get('state','?')}\")"
```
期望：Global=Local 且 Need=0，iPhone completion=100%。

**触发时机**：任何在 VPS 上新建目录的操作完成后，都需要手动 POST 一次 scan。

---

## 坑：文件夹路径必须完全一致

**症状**：`folder marker missing`，或设备连接但文件不同步。

**原因**：三方路径结构必须完全一致：
- VPS: `/home/wangsiji/projects/wsj-second-brain`
- Mac/iPhone: `~/.../wsj-second-brain`（不能只到父目录）

**排查步骤**：
```bash
# 1. 确认 VPS 上实际 vault 路径
ls /home/wangsiji/projects/wsj-second-brain/

# 2. 检查 .stfolder 标记文件是否存在（缺失会报 error）
ls /home/wangsiji/projects/wsj-second-brain/.stfolder

# 3. 如缺失则创建
mkdir -p /home/wangsiji/projects/wsj-second-brain/.stfolder

# 4. 检查同步状态
curl -s http://127.0.0.1:8384/rest/db/status?folder=obsidian-vault \
  -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa" | python3 -c "import sys,json; d=json.load(sys.stdin); print('state:', d['state'], 'need:', d['needTotalItems'])"
```

## iPhone + Obsidian 跨生态同步方案（核心方案）

**问题根源**：iPhone 上 Obsidian vault 在 iCloud 里，Syncthing 是独立 App 访问不了 iCloud 的沙箱目录，所以 Syncthing 指向 iCloud 目录永远无法同步。

**解决架构**：
- Mac ↔ iPhone：iCloud 原生同步（不需要 Syncthing）
- iPhone ↔ VPS：Obsidian 内置 WebDAV 直连 VPS（不需要 Syncthing）

### 第一步：在 VPS 上安装 WsgiDAV（iPhone Obsidian WebDAV 服务器）

```bash
pip install wsgidav cheroot --break-system-packages
```

### 第二步：启动 WebDAV 服务器

```bash
# 端口 8385，指向实际 vault 路径（当前: wsj-second-brain）
wsgidav --host=0.0.0.0 --port=8385 \
  --root=/home/wangsiji/projects/wsj-second-brain \
  --auth=anonymous
```

**验证**：
```bash
curl -s -X PROPFIND http://127.0.0.1:8385/ -H "Depth: 1" | head -5
# 应返回 XML，列出目录文件
```

### 第三步：iPhone Obsidian 配置

Obsidian → 设置 → 保险库 → 远程存储 → 添加 → WebDAV：
- 服务器：`http://VPS_IP:8385`
- 用户名/密码：留空（匿名）
- 保险库名：`wsj-second-brain`

### 已知限制
- 当前 WsgiDAV 无认证，建议配合防火墙只允许 iPhone IP 访问
- Syncthing 和 WsgiDAV 共存：Syncthing 同步 `wsj-second-brain` 目录，WsgiDAV 也指向同一目录，两套系统互不干扰

## 坑：Mac/iPhone 的 Obsidian 在 iCloud 里时的同步策略

**不要**让 Syncthing 直接同步 iCloud 目录，否则会与 iCloud 自己的同步冲突。

**正确架构**：
- Mac ↔ iPhone：走 iCloud 原生同步（不需要 Syncthing 介入）
- Mac → VPS：Syncthing 指向本地 vault 副本
- iPhone ↔ VPS：WebDAV（Obsidian 内置功能）

**Mac 上 Syncthing 文件夹路径**：
- ❌ `/Users/wangsiji/Library/Mobile Documents/iCloud~md~obsidian/Documents`（iCloud 目录，会冲突）
- ✅ `/Users/wangsiji/Library/Mobile Documents/iCloud~md~obsidian/Documents/wsj-second-brain`（本地 vault 副本）

**iPhone 上**：vault 路径通常在 Obsidian App 内设置，与 iCloud 同步目录一致即可。

## 参考：noVNC 远程桌面

如果需要在 VPS 上通过浏览器访问图形桌面（用于 iCloud-for-linux 等 GUI 应用），参考 `vps-remote-desktop` 技能。但 Syncthing 同步文件不需要图形界面，纯命令行即可。
