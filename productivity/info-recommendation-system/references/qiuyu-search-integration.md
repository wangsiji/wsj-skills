# 秋秋向量搜索 — Agent 对话集成

## 设置

- **项目位置**: `/home/wangsiji/projects/info-feed/`
- **搜索脚本**: `/home/wangsiji/projects/info-feed/qiuyu_search.py`（python3，返回 JSON）
- **CLI 快捷命令**: `~/.local/bin/qiuyu <关键词>`（bash 包装器，输出可读文本）
- **向量库位置**: `~/.hermes/qiuyu-vectordb/chroma.sqlite3`
- **大小**: 6,296 个片段 | 1,210 篇文章 | 1,986 万字 | ~245MB
- **数据来源**: `/home/wangsiji/projects/wsj-scrapy-gzh/` — 4个公众号：秋秋很开心(255篇)、秋秋在分享(227篇)、数字生命卡兹克(673篇)、六镇(55篇)，共1210篇
- **账号归属坑（2026-05-21修复）**: 旧版 `build_index.py` 用二元判断（"秋秋很开心" vs 其它→"秋秋在分享"），导致卡兹克和六镇的文章全被打成秋秋在分享。修复后需重建索引才生效

## 搜索脚本 qiuyu_search.py

```python
# 路径: ~/projects/info-feed/qiuyu_search.py
# 用法: cd ~/projects/info-feed && source .venv/bin/activate && python3 qiuyu_search.py <关键词>
#
# 输出: JSON 格式，包含 query, count, results[]
# 每个 result: {title, account, url, pub_date, score, preview, full_text}
```

关键参数：
- `TOP_K = 10` — 默认返回 10 条结果
- embedding: `all-MiniLM-L6-v2`（ChromaDB 内置，~79MB）
- 距离度量: cosine → `score = 1 - distance`

## 使用场景

### 写作查重
用户写新文章前问秋秋是否写过类似话题。搜索后输出：标题、来源公众号、原文链接、相关片段。

### 素材查找
写作过程中需要案例/金句/数据时搜索关键词，返回相关段落原文。

### 选题灵感
搜索宽泛关键词看秋秋写过哪些角度，找空白区或可续写的话题。

## agent 调用方式

每次搜索都需要激活 `.venv`，因为 chromadb 装在该 venv 下：

```python
# 在 execute_code 或 terminal 中：
import subprocess, json

result = subprocess.run([
    "python3", "/home/wangsiji/projects/info-feed/qiuyu_search.py", <query>
], capture_output=True, text=True, cwd="/home/wangsiji/projects/info-feed",
   env={**os.environ, "TF_CPP_MIN_LOG_LEVEL": "3"})

# 或通过 terminal 工具：
# cd /home/wangsiji/projects/info-feed && source .venv/bin/activate && python3 qiuyu_search.py <关键词>
```

## 索引重建

当新增文章时，重建索引：

```bash
cd /home/wangsiji/projects/info-feed
source .venv/bin/activate
python3 build_index.py  # 全量重建，~10-15 分钟
```

重建会扫描 `wsj-scrapy-gzh` 目录下的所有 `.md` 文件。

## 注意事项

- ChromaDB 需要 `.venv` 激活，`execute_code` 工具的沙箱没有 chromadb，必须走 `terminal`
- 嵌入模型第一次运行下载到 `~/.cache/chroma/onnx_models/`（约 79MB）
- 搜索质量取决于 chunk_size=1000 的切分粒度。短查询（如"FIRE"）效果比长查询好
- 同一篇文章可能有多个匹配片段（多段切分导致）
