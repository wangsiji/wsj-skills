# 从文章存档构建语义搜索知识库

当你有一堆爬下来的文章（微信导出 Markdown、网页抓取等），想用自然语言搜索而不是 grep 关键词时，可以用 ChromaDB 搭一个向量搜索引擎。

## 适用场景

- 公众号文章存档（微信导出，含内嵌 CSS）
- 博客/文章批量下载
- 个人知识库语义搜索
- 写新文章时查历史（"之前关于 XX 写过什么"）

## 完整流程

### 1. 安装依赖

```bash
pip install chromadb
```

ChromaDB 自带 all-MiniLM-L6-v2 嵌入模型（79MB），首次运行自动下载，无需额外配置。

### 2. 文章清洗

微信导出的 Markdown 有大量内嵌 CSS（第一行就是完整的 CSS 块），必须清理。

```python
import re

# 以 "原文地址:" 为界，取后面的正文（头部是标题+CSS）
parts = raw.split("原文地址:")
text = parts[1] if len(parts) > 1 else raw

# 去掉 HTML 标签
text = re.sub(r'<[^>]+>', '', text)

# 去掉图片标记 ![](url)
text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)

# 去掉 markdown 链接标记 [text](url)，只保留 text
text = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', text)

# 去掉图片链接行（mmbiz.qpic.cn 等）
# 去掉 "点击关注" 等推广语
```

### 3. 文章切分

平均每篇 10k-25k 字的文章需要切分成片段，每段约 1000 字 + 200 字 overlap：

```python
def chunk_article(article, chunk_size=1000, overlap=200):
    paragraphs = article["text"].split('\n')
    chunks = []
    # 按段落累积，超过 chunk_size 就切一块
    # 保留最后 3 段作为 overlap
    # ... (详见 build_index.py)
```

### 4. 构建索引

```python
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="/path/to/db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.create_collection(
    name="articles",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"},
)

# 每批 50 条添加
for i in range(0, len(chunks), 50):
    batch = chunks[i:i+50]
    collection.add(
        ids=[...],
        documents=[c["text"] for c in batch],
        metadatas=[{
            "title": c["title"],
            "account": c["account"],
            "url": c["url"],
            "pub_date": c["pub_date"],
        } for c in batch],
    )
```

### 5. 搜索

```python
results = collection.query(
    query_texts=["自由职业怎么赚钱"],
    n_results=10,
)
for doc_id, metadata, document, distance in zip(
    results["ids"][0], results["metadatas"][0],
    results["documents"][0], results["distances"][0]
):
    score = 1 - distance  # cosine 距离转相似度
    print(f"[{score:.0%}] {metadata['title']}")
```

### 6. 索引大小估算

| 文章数 | 平均字数 | 片段数 | 索引大小 |
|--------|---------|--------|---------|
| 500 | 10k | ~6,000 | ~240MB |
| 1000 | 10k | ~12,000 | ~500MB |

索引是 SQLite 文件（chroma.sqlite3），可以随时删除重建。

## 常见问题

### 嵌入模型下载慢

all-MiniLM-L6-v2 约 79MB，下载到 `~/.cache/chroma/onnx_models/`。如果 VPS 下载慢，可以手动下载放进去。

### 搜索不准确

- 减少 chunk_size：800 字每段效果更好
- 换更大的模型：all-mpnet-base-v2（420MB，效果更好但更慢）
- 用 API 嵌入：DeepSeek/Jina AI 的 embedding API，质量更高

### 索引构建慢

6299 片段在 CPU 上约 10-15 分钟。可以用更小的 batch_size（减少内存），或用 GPU 加速。

### 存储路径

索引文件建议放 `~/.hermes/` 下避免误删，或者放项目目录并加 .gitignore。
