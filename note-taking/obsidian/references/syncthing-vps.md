# Syncthing on VPS — Deployed 2026-05-04

## 部署状态

- **版本**：syncthing v2.0.16 "Hafnium Hornet"
- **二进制**：`/usr/local/bin/syncthing`
- **安装方式**：直接下载官方 tar.gz，非 apt（apt 版本可能较旧）
- **配置目录**：`/var/syncthing/`
- **同步文件夹**：`/home/wangsiji/syncthing/Obsidian`

## 启动方式

```bash
# 手动启动（已验证有效）
/usr/local/bin/syncthing serve \
  --home=/var/syncthing \
  --no-browser \
  --gui-address=0.0.0.0:8384

# 端口：8384（GUI/API），22000（数据，TCP+QUIC）
```

## 连接信息

| 项目 | 值 |
|------|-----|
| VPS 设备 ID | `XTMLFNH-LYUQY2I-XERNZRV-MOYENQA-PTTAM5X-O56DP5F-WSHVBWF-5WMC2AA` |
| GUI 地址 | `http://192.3.16.123:8384` |
| API Key | `m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa` |
| 数据端口 | 22000（TCP/QUIC，需防火墙开放） |

## systemd service（参考配置）

```
# /etc/systemd/system/syncthing@.service
# 注意：需要用 wangsiji 用户运行，否则 /var/syncthing 权限会报错
[Service]
User=wangsiji
ExecStart=/usr/local/bin/syncthing serve --home=/var/syncthing --no-browser --gui-address=0.0.0.0:8384
Restart=on-failure
ReadWritePaths=/home/wangsiji/syncthing /var/syncthing
```

## 常见问题

**Q: 进程启动后立刻退出（循环重启）**
A: 权限问题。检查 `/var/syncthing/` 归属是否正确：
```bash
sudo chown -R wangsiji:wangsiji /var/syncthing
```

**Q: 8384 端口已监听但浏览器打不开**
A: 检查是否有残留进程：`ps aux | grep syncthing`

**Q: 找不到 Device ID**
A: 从 cert.pem 提取：
```bash
openssl x509 -in /var/syncthing/cert.pem -noout -fingerprint
grep -oP 'device id="[^"]+"' /var/syncthing/config.xml
```

## 后续步骤（等待用户 Mac/iPhone 配置）

Mac 和 iPhone 安装 Syncthing 后，在 GUI 里添加 VPS 设备 ID，共享文件夹即可。

## API 用法

```bash
# 检查状态
curl -s -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa" \
  http://127.0.0.1:8384/rest/system/ping

# 查看配置
curl -s -H "X-API-Key: m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa" \
  http://127.0.0.1:8384/rest/system/config
```
