# 向量库搜索参考

## 位置

- DB：`~/.hermes/qiuqiu-vectordb/`（chroma，集合名 `qiuqiu_articles`）
- 脚本：本 skill 的 `scripts/search.py`
- venv：`~/projects/wsj-scrapy-gzh/.venv/`（含 chromadb）
- 文章文件目录：`~/projects/wsj-scrapy-gzh/《秋秋很开心》/` 和 `《秋秋在分享》/`

## 搜索命令

```bash
# 基础搜索
/home/wangsiji/projects/wsj-scrapy-gzh/.venv/bin/python3 \
  ~/.hermes/skills/creative/qiuqiu-content/scripts/search.py \
  "退休 旅居 花费" --limit 5

# 限定账号
... --account "秋秋在分享"

# 找真实数字：搜具体名词+数字
... "三亚 酒店 500 一月" --limit 3

# 找语气：搜口语特征词
... "我也 就是 哈哈" --limit 5
```

## 返回格式

```json
{
  "query": "搜索词",
  "count": 3,
  "results": [
    {
      "title": "文章标题",
      "account": "秋秋很开心",
      "pub_date": "2025-12-10",
      "url": "https://mp.weixin.qq.com/s/...",
      "score": 100.0,
      "text": "匹配段落前 400 字... "
    }
  ]
}
```

## 已知局限 & 补充策略

### 假阳性问题

向量库对**地名**（大理、威海、三亚等）和**高频词**（"学习"、"生活"、"每天"）搜素时，容易命中文末签名模板区域（"喜欢记得星标"、"粉丝微信：qiuqiu5261"），返回相似度虚高但内容无关的结果。

**解决：双路径互补**

| 路径 | 工具 | 适用场景 |
|------|------|---------|
| 向量库 | `scripts/search.py` | 语义匹配：找"旅居开销"这类抽象话题、找语气样本、找风格参考 |
| 文件系统 | `search_files` 通配符 | 精确匹配：找某个地名/事件出现了哪些文章，直接读全文 |

### 文件系统搜索命令

```bash
# 向量库搜完后，立即补文件搜索（在 Hermes 工具中）
search_files pattern="*大理*" target="files" path="~/projects/wsj-scrapy-gzh/"
search_files pattern="*旅居*" target="files" path="~/projects/wsj-scrapy-gzh/"
search_files pattern="*威海*" target="files" path="~/projects/wsj-scrapy-gzh/"
```

找到文章文件路径后，用 `read_file` 读全文获取完整内容。

### 为什么两条路径都要走

向量库返回的是 300 字段落片段 + 相似度分数，适合快速扫描"写过没有、怎么写的"。但文件名包含日期和标题关键词，精确匹配更可靠。**搜地名 → 两条路径都走，搜抽象话题（如"AI 提效"）→ 向量库为主。**

## 写稿流程中的位置

```
0a. 搜向量库 → 看写过没、怎么写的、有用过的数字没
0b. 搜地名/具体事件时 → 补文件系统搜索，找到文章读全文
1. 确认阶段+选题
2. 如需分析已发布文章 → down.mptext.top 下载全文
3. 写初稿
```
