---
name: wsj-server-infra
description: 自建服务器基础设施运维：当用户说"排查/部署/改反代/VNC 连不上/Syncthing 不同步/nginx 报错/Hermes Dashboard 异常/Web UI 起不来/Memory 侧车故障"时使用。服务器 192.3.16.123 | 域名 wangsiji.site。覆盖服务配置、反向代理、文件同步、远程桌面、TencentDB Agent Memory 侧车。
tags: [devops, nginx, hermes, syncthing, vnc]
version: 2.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [devops, nginx, hermes, syncthing, vnc]
    category: infra
---

# Self-Hosted Infrastructure

> 主文件只做路由 + 黄金规则。细节在 `references/`，按需读取。

## When to Use

- 用户要求运维/排查自建服务器（Hermes Dashboard、Web UI、nginx、Syncthing、VNC）
- 部署新服务、改反代配置、排查同步/远程桌面
- 服务器：192.3.16.123 | 域名 wangsiji.site

## Prerequisites

- SSH 访问服务器（凭证在 `.env`，不写死）
- 本地有 `~/.hermes` 与服务器配置对齐

---

## 黄金 5 条

1. 任何服务变更前先备份配置
2. 脚本极简：有变更执行、无变更静默；不画格式框、不记录 hash 对比
3. 凭证在 `.env`，不写死进 config 或 skill 内
4. 排查时先看 systemd 状态（`systemctl status`），再看 journalctl 日志
5. systemd --user 服务需登录用户 shell 生效

## Rule Priority（冲突时）

| 优先级 | 层 | 说明 |
|--------|----|------|
| **P0** | 配置可回滚 | 改 nginx / systemd 前备份；修改后 `nginx -t` 验证 |
| **P1** | 安全 | 不对外开放不必要端口；不暴露内网服务 |
| **P2** | 稳定优先 | 已知可用配置优先于升级新版本 |
| **P3** | 极简 | 脚本不写多余输出 |

## Task Router

```
用户说"排查XX/部署XX/改反代/VNC 连不上/Syncthing 不同步"
  ↓
A nginx 问题      → nginx -t → journalctl → references/nginx-config-template.md
B Dashboard/Web UI → systemctl status → references/hermes-dashboard-webui.md
C Syncthing 同步   → references/syncthing-sync.md
D VNC 连不上      → references/vnc-remote-desktop.md（4.1~4.5 启动/验证/排错）
E Memory 侧车     → references/memory-tencentdb-sidecar.md（6.1~6.7 凭证/端口/管线）
F Vision 报错     → references/vision-config.md → references/vision-troubleshoot.md
G 新服务部署      → 参考部署模式 + subpath-variant.md
```

## Never Do

- ❌ 改 nginx 配置不先 `nginx -t`
- ❌ 对外开放 Database/内部端口
- ❌ 脚本写多余输出（格式框/版本对比）
- ❌ systemd --user 服务不先确认用户 shell 有效

## Pre-flight Check

- [ ] 服务当前状态已确认（systemctl status / curl health）
- [ ] 需改的配置已备份
- [ ] 凭证路径已确认（`.env` not skill 内联）

## Post Check

- [ ] 服务正常运行（`systemctl status` / `curl :port`）
- [ ] nginx 配置 `nginx -t` 通过
- [ ] 无开放不必要端口

---

> 合并自：`self-hosted-infra` / `hermes-dashboard-setup` / `syncthing-setup` / `vps-remote-desktop`
> 服务器：192.3.16.123 | 域名：wangsiji.site

---

## 一、服务器概览

| 服务 | 端口 | 访问路径 | 管理方式 |
|------|------|---------|---------|
| Hermes Dashboard | 9119 | wangsiji.site/hermes/ | systemd (system-level) |
| Hermes Web UI | 8648 | wangsiji.site/webui/ | systemd (--user) |
| Hermes Gateway | 8642 | — | systemd (--user) |
| Syncthing GUI | 8384 | 本地 (SSH隧道) | systemd (--user) |
| Syncthing Data | 22000 | 对外 (relay 兜底) | — |
| noVNC (VNC桌面) | 6080 | 直接 IP:6080 | 手动启动 |
| WebDAV (iPhone同步) | 8385 | 对外 (匿名) | 手动启动 |

### 快速命令

```bash
systemctl status hermes-dashboard          # Dashboard
systemctl --user status hermes-web-ui       # Web UI
systemctl --user status hermes-gateway      # Gateway
systemctl --user status syncthing           # 文件同步
sudo nginx -s reload                        # 重载 nginx
sudo nginx -t                               # 检查 nginx 配置
sudo certbot renew                          # 续期 SSL
journalctl -u hermes-dashboard --since "24 hours ago"  # 看日志
```

## 二、Hermes Dashboard + Web UI

> 详细配置见 `references/hermes-dashboard-webui.md`。

## 三、Syncthing 文件同步

> 详细配置见 `references/syncthing-sync.md`。

## 八、脚本编写原则

本服务器的脚本遵循**极简原则**：只做必需的事，去掉格式化输出、版本对比、状态报告等噪音。

```
✅ 好：6 行，做完就停
cd /home/wangsiji/.hermes/hermes-agent
git pull --ff-only origin main 2>&1 || echo "已是最新"
source venv/bin/activate
uv pip install -e ".[all]" 2>&1

❌ 差：45 行，版本追踪 + 提交计数 + 格式框，噪音太多
```

**规则**：
- 有变更执行，没变更静默退出
- 不记录 old/new hash、commit count、tag 对比
- 不画格式框
- 错误直接 stderr，不需要 catch 后包装中文报告

## 参考文档

### 部署参考
- [nginx 配置模板](references/nginx-config-template.md)
- [nginx 静态文件服务](references/card-serving-nginx.md) — 知识卡片对外访问 + sites-enabled 注意事项
- [Web UI 部署记录](references/hermes-web-ui-deployment.md)
- [子路径部署变体](references/subpath-variant.md)
- [SSH 连接管理](references/ssh-connection-management.md)
- [自动更新崩溃恢复](references/auto-update-crash.md)

### Syncthing 参考
- [REST API 设备管理](references/syncthing-rest-api-device-management.md) — 用 API 添加/移除设备，替代 XML 编辑
- [WebDAV 设置](references/webdav-setup.md)
- [VPS 外部访问](references/vps-external-access.md)

### VNC 参考
- [VNC 远程桌面](references/vnc-remote-desktop.md) — 启动/验证/排错（4.1~4.5）
- [xdotool VNC 自动化](references/xdotool-vnc-automation.md)
- [systemd 常见问题](references/systemd-common-issues.md)
- [Vision 配置](references/vision-config.md)

### Memory 参考
- [memory-tencentdb 侧车](references/memory-tencentdb-sidecar.md) — 架构/凭证/管线/排错（6.1~6.7）

### 脚本
- [Syncthing 状态检查](scripts/syncthing-status.sh)
- [每日更新](scripts/daily-hermes-update.sh) — Hermes Agent + 官方 Dashboard + 第三方 Web UI 自动更新（cron 每天 4:00）
