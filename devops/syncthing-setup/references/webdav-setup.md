# WsgiDAV WebDAV 服务器参考

## 安装依赖
```bash
pip install wsgidav cheroot --break-system-packages
```

## 启动命令
```bash
wsgidav --host=0.0.0.0 --port=8385 \
  --root=/home/wangsiji/projects/wsj-second-brain \
  --auth=anonymous
```

## 验证
```bash
# 列出目录
curl -s -X PROPFIND http://127.0.0.1:8385/ -H "Depth: 1"

# 获取文件内容
curl -s http://127.0.0.1:8385/test.md
```

## 已知问题

### Cheroot 缺失
- 错误：`ModuleNotFoundError: No module named 'cheroot'`
- 解决：`pip install cheroot --break-system-packages`

### Apache2 端口占用（不可用）
- Apache2 默认占 80 端口，且不支持在 `<VirtualHost>` 内直接写 `DAV On`
- 改用 WsgiDAV 更简单可靠

## 开机自启
如需后台运行，可用 systemd 服务或 screen/nohup
