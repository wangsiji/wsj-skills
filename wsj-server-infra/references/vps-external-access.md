# Syncthing VPS 外部访问问题排查

## 症状
- `ps aux` 显示 syncthing 进程在跑
- `curl localhost:8384` 返回 200
- 但外部客户端（Mac/iPhone）连不上
- `curl http://VPS_IP:8384` 失败（exit code 7）

## 排查路径
```bash
# 1. 检查端口绑定
ss -tlnp | grep 8384
# 期望看到 *:8384 或 0.0.0.0:8384
# 如果看到 127.0.0.1:8384 → 只监听本地，外网不通

# 2. 检查 config.xml 中的 gui address
grep -E 'gui|address' /var/syncthing/config.xml | head -10

# 3. 检查云服务器安全组是否开放 8384
```

## 根因
config.xml 中 `<gui><address>127.0.0.1:8384</address></gui>` 只监听本地回环接口，即使进程启动时传了 `--gui-address=0.0.0.0:8384`，部分版本也不会覆盖 config.xml 的值。

## 修复
```bash
# 修改 config.xml
sed -i 's|<address>127.0.0.1:8384</address>|<address>0.0.0.0:8384</address>|' /var/syncthing/config.xml

# 重启
pkill -9 -f syncthing
sleep 1
syncthing serve --home=/var/syncthing --no-browser --gui-address=0.0.0.0:8384
```

## 云服务器安全组
腾讯云/阿里云等需要在控制台手动添加入站规则：
- 端口：8384
- 协议：TCP
- 来源：0.0.0.0/0（或限定 IP）
