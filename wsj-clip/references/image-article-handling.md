# 图片型公众号文章处理

部分公众号文章是纯图片形式（一张张截图拼成的文章），`format=markdown` 只返回 CSS，正文为空。

## 识别特征

调用 `format=json` 获取元数据后，检查以下信号：

| 信号 | 说明 |
|------|------|
| `item_show_type` = 8 | 图片文章标记 |
| `picture_page_info_list` 非空 | 包含 N 个图片对象，每个有 `cdn_url` |
| `content_noencode` 很短（<50字） | 仅为文章描述，非正文 |
| `format=text` 返回空 | 无文字内容可提取 |

示例（段继芳的小屋 · NotebookLM 提示词合集）：
- `item_show_type`: 8
- `picture_page_info_list`: 9 张 1242x1656 的截图
- `content_noencode`: "用这套提示词，5分钟吃透一本书的提示词合集"（仅描述）

## 处理流程

```bash
# 1. 获取图片列表
curl -s "https://down.mptext.top/api/public/v1/download?url=<URL>&format=json" |
  python3 -c "
import json, sys
data = json.load(sys.stdin)
images = data.get('picture_page_info_list', [])
for i, img in enumerate(images):
    print(img['cdn_url'].split('?')[0].replace('&amp;','&'))
"

# 2. 下载到 assets/ 目录
mkdir -p "assets"
i=1
for url in $(cat urls.txt); do
  curl -sL "$url" -o "assets/$(printf '%02d' $i).jpg"
  i=$((i+1))
done

# 3. OCR 封面页（tesseract + chi_sim 中文包）
tesseract assets/01.jpg - -l chi_sim 2>/dev/null
# 注意：正文截图通常 OCR 效果差，仅封面页可识别

# 4. 写入 Markdown（含图片）
```

## 文件结构

```
Raw/Focus/GZH/{公众号名称}/
├── YYYYMMDD_标题.md
└── assets/
    ├── 01.jpg
    ├── 02.jpg
    ...
    └── NN.jpg
```

## Markdown 模板

```markdown
---
category:
  - "[[公众号]]"
author:
  - "[[{作者名}]]"
url: "{URL}"
tags: [剪藏, 公众号]
created: YYYYMMDD
modified: YYYYMMDD
---

# {标题}

> {描述文字}

## AI 智能总结

本文为图片形式，共 N 页截图，内容为【简要概述】。

## 原文（图片文章）

本文章为图片形式，共 N 页截图：

**第 1 页**
![page-01](assets/01.jpg)

**第 2 页**
![page-02](assets/02.jpg)

...

**第 N 页**
![page-NN](assets/NN.jpg)

## 关于作者

> {作者签名}
```

## 已知限制

| 项 | 说明 |
|----|------|
| **OCR** | 仅封面页（第1张）可识别标题，正文截图的文字识别率极低 |
| **getnote AI 总结** | 图片文章 getnote 通常返回空 content，AI 总结不可用 |
| **图片质量** | 微信压缩后 1242x1656 的 jpg，每张 ~200-300KB |
| **写入毛豆不记** | 图片存在毛豆不记 Markdown 文件中无法直接显示，需在 Obsidian 或浏览器打开 |
