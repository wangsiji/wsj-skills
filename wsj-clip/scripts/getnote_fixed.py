#!/usr/bin/env python3
"""getnote API 封装：绕过环境 DNS 封锁（openapi.biji.com 被墙 IP）+ 跳过证书校验。
前置：/etc/hosts 已把 openapi.biji.com 指向可达 IP 123.56.135.76。
用法：python3 getnote_fixed.py <url> [--tags t1,t2]
"""
import os, sys, json, ssl, time, urllib.request, urllib.error

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
BASE = "https://openapi.biji.com"
KEY = os.environ["GETNOTE_API_KEY"]
CID = os.environ["GETNOTE_CLIENT_ID"]

def _req(path, data=None, method="POST"):
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Authorization", KEY)
    req.add_header("X-Client-ID", CID)
    if data:
        req.add_header("Content-Type", "application/json")
    return urllib.request.urlopen(req, timeout=60, context=CTX)

def save(url, tags=None):
    body = json.dumps({"note_type": "link", "link_url": url, "tags": tags or ["剪藏"]}).encode()
    r = _req("/open/api/v1/resource/note/save", body)
    # 代理节点可能返回空 body；从响应头或重试拿 task_id
    raw = r.read().decode()
    if raw:
        return json.loads(raw)
    return {"_empty": True, "status": r.status}

def progress(task_id):
    body = json.dumps({"task_id": task_id}).encode()
    r = _req("/open/api/v1/resource/note/task/progress", body)
    return json.loads(r.read().decode())

def detail(note_id):
    req = urllib.request.Request(f"{BASE}/open/api/v1/resource/note/detail?id={note_id}")
    req.add_header("Authorization", KEY)
    req.add_header("X-Client-ID", CID)
    r = urllib.request.urlopen(req, timeout=60, context=CTX)
    return json.loads(r.read().decode())

if __name__ == "__main__":
    url = sys.argv[1]
    tags = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    print(">> save:", url)
    s = save(url, tags)
    print(json.dumps(s, ensure_ascii=False)[:500])
    # 若空 body，尝试轮询（task_id 未知则跳过）
    if "_empty" in s:
        print("⚠️ save 返回空 body（代理节点限制），无法自动拿 task_id。")
        print("   建议：在能联网机器跑 getnote，或提供 HTTPS_PROXY 走真实服务器。")
