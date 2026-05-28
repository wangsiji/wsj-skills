# VPS 上 systemd 常见问题

## 216/GROUP — Failed to determine supplementary groups

**症状**：
```
systemctl --user start my-service
# Status: 216/GROUP
# Journal: Failed to determine supplementary groups: Operation not permitted
```

**原因**：`/etc/nsswitch.conf` 中 `group:` 行包含 `winbind`：
```
group:  files systemd winbind
```

当 winbind 服务未运行（大多数 VPS 没有 AD 域集成），systemd 用户服务在查询补充组时会失败。这是 `systemctl --user` 模式的已知限制。

**解决方案**：改用系统级 service（root 运行），明确指定用户：

```ini
[Unit]
Description=My Service
After=network.target

[Service]
Type=simple
User=wangsiji
ExecStart=/path/to/script.sh
WorkingDirectory=/home/wangsiji
Restart=on-failure
RestartSec=10

# 关键：清空 SupplementaryGroups 避免 NSS 查询
SupplementaryGroups=

[Install]
WantedBy=multi-user.target
```

```bash
# 复制到系统目录
sudo cp my-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable my-service
sudo systemctl start my-service
```

**不用动 `/etc/nsswitch.conf`** — 改这个文件影响整个系统的组解析，风险太大。用系统级 service 绕过去就行。

## 常见 systemd 用户服务备用方案

| 问题 | 方案 |
|------|------|
| 216/GROUP (winbind 未运行) | 改用系统级 service + User= + SupplementaryGroups= |
| 服务在 SSH 断开后停止 | `sudo loginctl enable-linger $USER` |
| 服务启动太快，依赖的网络还没就绪 | 加 `After=network-online.target` 和 `Wants=network-online.target` |
| ExecStart 路径用到 venv 里的 python | 建议写 bash wrapper 脚本 source venv 后再 exec，比直接在 ExecStart 里拼路径更可靠 |
