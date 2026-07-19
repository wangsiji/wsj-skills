#!/bin/bash
# Syncthing VPS 端状态快速检查脚本
# 用法: bash syncthing-status.sh

API_KEY="m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa"
BASE="http://127.0.0.1:8384"

echo "=== Syncthing 状态检查 ==="

# 1. 进程是否在跑
echo -e "\n[1] 进程状态:"
ps aux | grep 'syncthing serve' | grep -v grep || echo "⚠️  进程未运行"

# 2. API 是否响应
echo -e "\n[2] API 响应:"
PING=$(curl -s "$BASE/rest/system/ping" 2>/dev/null)
if [ "$PING" = '{"ping":"pong"}' ]; then
    echo "✅ API 正常"
else
    echo "⚠️  API 无响应: $PING"
fi

# 3. 设备连接状态
echo -e "\n[3] 设备连接状态:"
curl -s "$BASE/rest/system/connections" -H "X-API-Key: $API_KEY" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
for k, v in d.get('connections', {}).items():
    name = k[-8:]
    status = '✅' if v.get('connected') else '❌'
    in_b = v.get('inBytesTotal', 0)
    out_b = v.get('outBytesTotal', 0)
    print(f'  {status} {name}: in={in_b} out={out_b}')
" 2>/dev/null || echo "无法获取设备状态"

# 4. 文件夹同步状态
echo -e "\n[4] 文件夹同步状态:"
curl -s "$BASE/rest/db/status?folder=obsidian-vault" -H "X-API-Key: $API_KEY" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
state = d.get('state', 'unknown')
global_files = d.get('globalFiles', 0)
need = d.get('needTotalItems', 0)
print(f'  状态: {state}')
print(f'  全局文件: {global_files}')
print(f'  待同步: {need}')
" 2>/dev/null || echo "无法获取文件夹状态"

echo -e "\\n[5] 磁盘空间:\"\nDISK=$(df -h / | tail -1 | awk '{print $5}')\nif [ \"${DISK%'%'}\" -gt 95 ]; then\n    echo \"❌ 磁盘已满: $DISK 使用率（Syncthing 需 < 99%）\"\nelif [ \"${DISK%'%'}\" -gt 90 ]; then\n    echo \"⚠️  磁盘紧张: $DISK 使用率\"\nelse\n    echo \"✅ 磁盘: $DISK 使用率\"\nfi\n\n# 6. WebDAV 是否可用
echo -e "\n[5] WebDAV (端口 8385):"
WEBDAV=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8385/ 2>/dev/null)
if [ "$WEBDAV" = "200" ] || [ "$WEBDAV" = "207" ]; then
    echo "✅ WebDAV 正常 (HTTP $WEBDAV)"
else
    echo "⚠️  WebDAV 异常 (HTTP $WEBDAV)"
fi

echo ""
