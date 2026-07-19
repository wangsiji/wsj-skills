# Syncthing REST API 设备管理

> 优先用 REST API 操作，避免直接编辑 XML。

## 准备

```bash
# API Key 在 config.xml 中
APIKEY=$(grep -oP '(?<=<apikey>)[^<]+' /var/syncthing/config.xml)
BASE="http://127.0.0.1:8384/rest/system/config"
```

## 查看设备列表

```bash
curl -s -H "X-API-Key: $APIKEY" "$BASE" | python3 -c "
import json, sys
cfg = json.load(sys.stdin)
for d in cfg['devices']:
    print(f\"{d['name']:20s}  {d['deviceID'][:16]}...\")
"
```

## 添加设备

```bash
curl -s -H "X-API-Key: $APIKEY" "$BASE" | python3 -c "
import json, sys
cfg = json.load(sys.stdin)

new_dev = {
    'deviceID': 'DEVICE_ID_GOES_HERE',
    'name': 'iPhone',
    'addresses': ['relay://global'],
    'compression': 'metadata',
    'introducer': False,
    'autoAcceptFolders': True,
    'paused': False
}
cfg['devices'].append(new_dev)
for f in cfg['folders']:
    f['devices'].append({'deviceID': new_dev['deviceID'], 'introducedBy': ''})
print(json.dumps(cfg))
" | curl -s -X POST -H "X-API-Key: $APIKEY" -H "Content-Type: application/json" -d @- "$BASE"

# 重载
curl -s -X POST -H "X-API-Key: $APIKEY" http://127.0.0.1:8384/rest/system/restart
```

## 移除设备

```python
# 两步法（先用 Python 改，再 POST）
MAC_ID = 'WKSGWKA-ZXSUTMY-QIF4OZC-MBUCZ7J-6OFLRV2-W7QRVP5-4WGRKBT-YTKOLAT'

import json, urllib.request
APIKEY, BASE = "xxx", "http://127.0.0.1:8384/rest/system/config"

req = urllib.request.Request(BASE, headers={"X-API-Key": APIKEY})
cfg = json.load(urllib.request.urlopen(req))

cfg['devices'] = [d for d in cfg['devices'] if d['deviceID'] != MAC_ID]
for f in cfg['folders']:
    f['devices'] = [d for d in f['devices'] if d['deviceID'] != MAC_ID]

data = json.dumps(cfg).encode()
req2 = urllib.request.Request(BASE, data=data, method='POST',
    headers={"X-API-Key": APIKEY, "Content-Type": "application/json"})
urllib.request.urlopen(req2)

urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:8384/rest/system/restart",
    method='POST', headers={"X-API-Key": APIKEY}))
```

## 验证

```bash
curl -s -H "X-API-Key: $APIKEY" http://127.0.0.1:8384/rest/system/connections | \
  python3 -c "
import json, sys
for d in json.load(sys.stdin)['connections']:
    print(f\"{d[:16]}...\")
"
```

## 注意

- 必须用 POST，PUT 会返回 405 Method Not Allowed
- 改完后需要 restart 生效（POST restart 接口返回 `{"ok": "restarting"}`）
- 设备和文件夹的关联要一起处理，只删设备不删文件夹里的引用会遗留孤儿记录
