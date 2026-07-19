#!/usr/bin/env python3
"""
搜索秋秋向量库 — 给定关键词，返回最相关的段落。
用法: python3 search.py "关键词" [--limit 5] [--account 秋秋很开心]

输出 JSON: {query, count, results: [{title, account, pub_date, url, score, text}]}
"""
import sys, json
import chromadb
from chromadb.config import Settings

VECTORDB_DIR = "/home/wangsiji/.hermes/qiuqiu-vectordb"
TARGET_ACCOUNTS = ["秋秋很开心", "秋秋在分享"]

query = sys.argv[1] if len(sys.argv) > 1 else ""
limit = 5
account_filter = ""
args = sys.argv[2:]
for i, a in enumerate(args):
    if a == "--limit" and i + 1 < len(args):
        limit = int(args[i + 1])
    if a == "--account" and i + 1 < len(args):
        account_filter = args[i + 1]

if not query:
    print(json.dumps({"error": "需要一个搜索关键词"}, ensure_ascii=False))
    sys.exit(1)

client = chromadb.PersistentClient(path=VECTORDB_DIR)
collection = client.get_collection("qiuqiu_articles")

where = None
if account_filter:
    where = {"account": account_filter}

results = collection.query(
    query_texts=[query],
    n_results=limit * 3,  # 多拉一些，过滤非秋秋号
    include=["metadatas", "documents"],
    where=where,
)

output = []
seen_articles = set()

for i, (meta, doc) in enumerate(zip(results["metadatas"][0], results["documents"][0])):
    # 过滤只看秋秋号
    if meta.get("account") not in TARGET_ACCOUNTS:
        continue

    art_key = meta.get("filepath", f"{meta.get('title')}_{meta.get('pub_date')}")
    if art_key in seen_articles:
        continue
    seen_articles.add(art_key)

    output.append({
        "title": meta.get("title", ""),
        "account": meta.get("account", ""),
        "pub_date": meta.get("pub_date", ""),
        "url": meta.get("url", ""),
        "score": round(1.0 / (i + 1) * 100, 1),
        "text": doc[:400],
    })

    if len(output) >= limit:
        break

print(json.dumps({"query": query, "count": len(output), "results": output}, ensure_ascii=False))
