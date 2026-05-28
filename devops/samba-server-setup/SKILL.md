---
name: samba-server-setup
description: Samba server setup on Debian (port 8445), password config, and common issues
category: devops
---

# Samba Server Setup (Debian)

## 已知环境
- 端口：**8445**（非默认445）
- OS: Debian Trixie
- 已装好 samba（`apt install samba`）

## 正确启动顺序

SMB 密码设置必须在服务运行状态下进行，否则 `smbpasswd` 报 "Unable to get new password"。

```bash
# 1. 清理残留进程
sudo killall -9 smbd nmbd 2>/dev/null; sleep 1

# 2. 启动服务
sudo systemctl start smbd
sleep 3
sudo systemctl is-active smbd  # 确认 active

# 3. 设密码（用 heredoc 避免交互）
sudo smbpasswd -a wangsiji << 'EOF'
你的密码
你的密码
EOF

# 4. 验证
sudo pdbedit -L | grep wangsiji
smbclient -L localhost -p 8445 -N
```

## 连接方式（从局域网访问）
- 地址: `服务器IP:8445`
- 用户: `wangsiji`
- 密码: 同系统登录密码（或上面设的）

## 常见问题

### "Unable to get new password"
原因：smbd 服务未运行。解决：先 `sudo systemctl start smbd`

### 服务启动超时/卡死
用 `killall -9 smbd nmbd` 清理残留进程后重试

### 服务被 OOM Killer 杀掉（内存不足的 VPS）
考虑降低 smbd 进程数或加 swap

## 添加自定义共享目录
编辑 `/etc/samba/smb.conf`，在 `[global]` 后加：
```
[share_name]
   path = /path/to/folder
   browseable = yes
   read only = no
   guest ok = no
   valid users = wangsiji
```
然后 `sudo systemctl restart smbd`
