# down.mptext.top — 公众号文章导出 API & 自动同步

> 发现于 2026-06-05 剪藏 session。2026-06-15 发现文章列表 API + 自动同步能力。

## 服务概述

公众号文章导出平台，提供公开 API 可直接下载公众号文章内容。
**技术栈**：Nuxt 3 SPA，Cloudflare 托管

## 关键接口

### 1. 搜索公众号（需 API Key）

```
GET /api/public/v1/account?keyword={关键词}&begin=0&size=5
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `keyword` | 是 | 公众号名称或关键字 |
| `begin` | 否 | 起始索引（默认 0） |
| `size` | 否 | 返回条数（默认 5，最大 20） |

返回 fakeid，供文章列表接口使用。

### 2. 获取历史文章列表（需 API Key）

```
GET /api/public/v1/article?fakeid={公众号id}&begin=0&size=20
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `fakeid` | 是 | 公众号id（从 /account 接口获取） |
| `begin` | 否 | 起始索引（默认 0） |
| `size` | 否 | 返回条数（默认 5，最大 20，一条消息可能含多篇文章） |

### 3. 下载文章（无需 API Key）

```
GET /api/public/v1/download?url={url_encoded}&format=markdown
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `url` | 是 | 文章链接，需 URL 编码 |
| `format` | 否 | 输出格式：html / markdown / text / json |

**无需 API 密钥**，可直接调用。

### 4. 根据文章链接查公众号（需 API Key）

```
GET /api/public/v1/accountbyurl?url={url_encoded}
```

### 5. 查询公众号主体信息（无需 API Key，beta）

```
GET /api/public/beta/authorinfo?fakeid={公众号id}
```

## Markdown 输出格式与清理（手动剪藏用）

`format=markdown` 输出的内容在合并进最终文件前**必须清理**。原始输出包含 CSS 噪声、封面图链接、重复 H1（`=====` 下划线格式）和平台界面文本。

**清理顺序（⚠️ 旧正则已失效，下面是 2026-07-18 实测可工作的版本）：**

> ⚠️ 旧文档的 `re.sub(r'^#js\\_row.+?^$\\n', ...)` **完全不命中** —— 实际 API 返回的 CSS 是**单行**（`#js\_row\_immersive\_stream\_wrap { max-width: 667px; ... }`），没有尾随空行，按上面那行去删会把整段 CSS 留在正文开头。正确做法是按行特征过滤。

```python
import re

# 1. 删 CSS 行：含 'max-width' 且含 '{' 的那一长串样式行
lines = body.split('\n')
body = '\n'.join(ln for ln in lines if not ('max-width' in ln and '{' in ln))
# 2. 删封面图行（转义形式是 ![cover\_image]）
body = re.sub(r'^!\[cover\\_image\].*$\n?', '', body, flags=re.MULTILINE)
# 3. 删重复的 ==== 式 H1（标题 + 下划线）
body = re.sub(r'^.+\n=+\n?', '', body, flags=re.MULTILINE)
# 4. 删平台杂项
body = re.sub(r'^原创 .+$\n?', '', body, flags=re.MULTILINE)
body = re.sub(r'^在小说阅读器读本章.*$\n?', '', body, flags=re.MULTILINE)
body = re.sub(r'^去阅读\s*$', '', body, flags=re.MULTILINE)
body = re.sub(r'^在小说阅读器中沉浸阅读\s*$', '', body, flags=re.MULTILINE)
# 5. 合并 3+ 空行
body = re.sub(r'\n{3,}', '\n\n', body)
body = body.strip()
# 6. 若上面的清理吃掉了 H1，补一个
if not body.startswith('# '):
    body = f'# {title}\n\n{body}'
```

清理后的 body 应以 `# ` 开头，不含 CSS 或界面文本。

**推荐路径**：把 down.mptext.top 的原始 markdown **直接喂给 `merge-clip.py`**，不要自己先清理再喂。脚本内部已带一份精简 cleanup（`cover_image` / `原创` / `往期回顾` 等），双重清理会丢内容。只有需要自定义时才手动清理。

## API Key 获取 & 认证方式

### 获取

1. 打开 https://down.mptext.top/dashboard/api
2. 点"查询 API 密钥"按钮（需先微信扫码登录）

### 认证方式

支持两种方式（二选一）：

**a. 请求头（推荐）：**
```
X-Auth-Key: {你的API密钥}
```

**b. Cookie：**
```
auth-key={你的API密钥}
```

⚠️ API 密钥和网站登录绑定——扫码登录后会自动刷新密钥。登录失效时密钥也失效。

## 自动同步流程

### 脚本

已部署在 Hermes，定时检测公众号新文章并下载。

```bash
# 增量模式（默认）：只下载最近 3 个月且本地没有的文章
python3 ~/.hermes/scripts/sync_qiuqiu_articles.py

# 全量模式：扫全部历史文章，跳过已有文件
python3 ~/.hermes/scripts/sync_qiuqiu_articles.py --full
```

### Cron 配置

每天 06:00 AM 自动运行（no_agent 模式，不消耗 LLM token）：

```
Cron: 0 6 * * *
Job: sync-qiuqiu-articles
Script: sync_qiuqiu_articles.py
Mode: no_agent (script stdout → deliver verbatim)
Config: 每日自动，有新文章时通知
```

### 支持的公众号

| 公众号 | fakeid | 本地目录 |
|--------|--------|---------|
| 秋秋很开心 | MzI4NzU3ODk5NQ== | `~/projects/wsj-scrapy-gzh/《秋秋很开心》` |
| 秋秋在分享 | MzU3MDM3ODc2NQ== | `~/projects/wsj-scrapy-gzh/《秋秋在分享》` |

检测公众号是否有新文章发布，自动抓取到本地。

### 前提

- 在 down.mptext.top 的 **公众号管理** 中添加了目标公众号
- Dashboard 会自动同步文章（显示同步范围）

### 执行步骤

```
1. 获取 API Key → 调 /article 获取最新5篇文章列表
2. 提取每篇的 URL + 标题 + 时间
3. 对比本地文件名（日期前缀 + 标题相似度匹配）
4. 发现新文章 → 调 /download?format=markdown 下载
5. 保存到对应目录
6. 如有新文章 → 自动重建向量索引
```

### 去重逻辑

按 `(日期, 简化标题)` 匹配，不是单纯按日期范围：

```python
# 本地已有文件的 key 集合
existed = set()
for fname in os.listdir(local_dir):
    m = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)\.md$', fname)
    if m:
        title_key = m.group(2).lower().replace('_','').replace('，','').replace(',','')
        existed.add((m.group(1), title_key))

# API 文章只下载没匹配上的
new_articles = []
for art in api_articles:
    date = datetime.fromtimestamp(art['update_time']).strftime('%Y-%m-%d')
    t = re.sub(r'[\s,，！!？?、—\.]', '', art['title'].lower())
    if (date, t) not in existed:
        new_articles.append(art)
```

### 向量索引联动

新文章下载完成后，自动触发本地索引重建：

```python
# sync 脚本尾部
if len(new_articles) > 0:
    subprocess.run([
        "/home/wangsiji/projects/wsj-scrapy-gzh/.venv/bin/python3",
        "/home/wangsiji/projects/wsj-scrapy-gzh/build_vector_index.py"
    ])
```

索引脚本位置：`/home/wangsiji/projects/wsj-scrapy-gzh/build_vector_index.py`
索引输出：`~/.hermes/qiuqiu-vectordb/`，集合名 `qiuqiu_articles`

### 下载保存

```python
import urllib.request, json, urllib.parse, os, re

url_encoded = urllib.parse.quote(article_url)
api_url = f"https://down.mptext.top/api/public/v1/download?url={url_encoded}&format=markdown"
resp = urllib.request.urlopen(api_url)
markdown_content = resp.read().decode('utf-8')

meta_url = f"https://down.mptext.top/api/public/v1/download?url={url_encoded}&format=json"
meta_resp = urllib.request.urlopen(meta_url)
meta = json.loads(meta_resp.read())
title = meta.get('title', '')
safe_title = re.sub(r'[\\/:*?"<>|]', '', title).replace(' ', '_')[:80]

filename = f"{date_str}_{safe_title}.md"
with open(f"{local_dir}/{filename}", 'w', encoding='utf-8') as f:
    f.write(markdown_content)
```

## 图片文章（picture_page_info_list）处理

部分公众号文章以纯图片形式发布。JSON 格式返回含 `picture_page_info_list[]` 字段：

```json
"item_show_type": 8,
"picture_page_info_list": [
  {
    "cdn_url": "https://mmbiz.qpic.cn/.../0",
    "width": 1242,
    "height": 1656
  }
]
```

### 检测

```python
# 调 format=json 后检查
data = json.loads(response)
is_image_article = bool(data.get("picture_page_info_list"))
if is_image_article:
    print(f"图片文章：{len(data['picture_page_info_list'])} 页")
```

### 图片 URL 清洗

`cdn_url` 中的 `&amp;` 需替换为 `&`，URL 中 `wx_fmt=jpeg&from=appmsg` 参数不影响下载，可直接用。

```python
raw_url = img["cdn_url"]
clean_url = raw_url.replace("&amp;", "&").split("?")[0]
# 或保留全部参数：raw_url.replace("&amp;", "&")
```

### 下载到 assets/

```bash
mkdir -p "Raw/Focus/GZH/{作者名}/assets"
for i in "${!urls[@]}"; do
    idx=$(printf "%02d" $((i+1)))
    curl -sL "${urls[$i]}" -o "assets/${idx}.jpg"
done
```

### OCR 尝试

```bash
tesseract assets/01.jpg - -l chi_sim
```

— 纯图片文章的 OCR 通常只能识别封面标题页（大字+白底），正文截图（带复杂背景/渐变色/特殊字体）识别率很低。不要过度依赖 OCR。

### format 行为差异

| format | 对图片文章的反应 |
|--------|-----------------|
| `markdown` | 只返回 CSS（无法提取正文）|
| `json` | 含 `picture_page_info_list[]` + metadata |
| `text` | 返回空 |

这是正常行为。如果 `format=markdown` 只有 CSS，不要降级到 curl+UA（会触发 CAPTCHA），直接用 `format=json` 处理。

| 场景 | curl+UA 方案 | down.mptext.top API |
|------|-------------|---------------------|
| 标准文章 | ✅ | ✅ |
| 分享页/CAPTCHA | ⚠️ content_noencode 兜底 | ✅ 全过 |
| 输出格式 | 自写 HTML→MD 转换 | 原生 markdown/text/json |
| 批量同步 | ❌ 需手动发链接 | ✅ 文章列表 → 批量下载 |
| 依赖 | 无 | 外部 API（免费，可能后收费） |

## 排错

### 症状：API 返回 0 篇文章（sync 脚本输出「已是最新」但实际有新文章）

**原因：** API Key 失效，`/article` 和 `/account` 接口返回 `"base_resp":{"ret":-1,"err_msg":"认证信息无效"}`。Key 与网站登录绑定，退出登录/登录过期后自动失效。

**诊断：**
```bash
# 直调 API 看响应（非 200 或含 ret=-1 = 认证失效）
curl -s "https://down.mptext.top/api/public/v1/article?fakeid=MzI4NzU3ODk5NQ==&size=5&begin=0" \
  -H "X-Auth-Key: $API_KEY" | python3 -m json.tool | head -10
```

**恢复：**
1. 打开 https://down.mptext.top/dashboard/api
2. 微信扫码重新登录
3. 点「查询 API 密钥」获取新 Key
4. 更新 `~/.hermes/scripts/sync_qiuqiu_articles.py` 中的 `API_KEY` 变量
5. 用新 Key 手动跑一次同步验证

**预防：** 每月检查一次 API Key 有效性，登录失效时建议重新扫码。

### 症状：单篇下载失败（HTTP 非 200）

检查文章链接是否可公开访问（公众号设为「禁止转载」的帖子可能无法导出）。降级到 curl + 移动端 UA 方案。

## 注意

- 当前免费，后续可能改为收费模式
- 大调用量建议私有部署
- `/download` 接口无需 API Key，可作为单个链接抓取的兜底方案
- `/article` 和 `/account` 需要 API Key
