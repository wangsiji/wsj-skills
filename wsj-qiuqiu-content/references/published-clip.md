# 成稿抓取流程（Published Clip）

> 抓取「秋秋很开心」已发表文章，存入初稿目录，供草稿对比 / 润色分析用。

## 适用场景

- 用户说"抓这篇成稿""把某篇秋秋文章存进来""对比草稿和成稿"
- 需要从线上已发表文章提取正文，与本地草稿做对比分析

## 核心规则

**复用 wsj-clip 的 mptext API 提取，但落点改为初稿目录，不用 Raw/。**

- wsj-clip 是手写 skill，本流程不修改它代码，只复用其 API 端点与清洗逻辑
- 成稿落点：`00-LLM-WiKi/Outputs/秋秋很开心初稿/`
- 文件内统一三段式：`## 初稿` / `## AI 智能总结` / `## 成稿`

## 执行脚本

```
python3 scripts/clip_qiuqiu_published.py <文章URL> [--name 自定义名]
```

脚本逻辑：
1. `GET down.mptext.top/api/public/v1/download?url=<encoded>&format=html` 抓正文（游客可用，markdown 需会员）
2. `GET ...&format=json` 拿 metadata（标题等）
3. 清洗 HTML → 干净 Markdown（按 wsj-clip 清洗规则：去 CSS/噪音行/连续空行）
4. 写三段式文件，frontmatter 含 `name/description:图：@秋秋/category:[[自媒体：秋秋很开心]]/tags/url/published(空待填)`

## 文件格式（成稿抓取产物）

```markdown
---
name: 秋秋很开心_成稿_xxx
description: 图：@秋秋
category:
  - "[[自媒体：秋秋很开心]]"
tags: [秋秋很开心, 成稿]
click:
url: <文章链接>
published:
---

## 初稿

> 待填写（草稿底稿）

---

## AI 智能总结

> 待填写（成稿要点提炼）

---

## 成稿

<线上正文>
```

## 与草稿合并

若本地已有该篇草稿（如 `秋秋很开心_初稿_xxx.md`），抓取后有两种处理：
- **新建独立成稿文件**：适用于首次抓取，草稿另存
- **合并进已有草稿文件**：把成稿段追加到草稿文件的 `## 成稿` 位置，保持初稿/AI智能总结/成稿同文件（当前 5 篇已用此结构）

## 注意事项

- `published` 字段 API 不返回，需手动填（或接带 Key 的 /article 接口）
- `click`（阅读量）来自用户手动填写，不在抓取范围
- 图片文章（item_show_type=8）API markdown 只返回 CSS，需改用 json 的 picture_page_info_list + OCR（参考 wsj-clip references/down-mptext-api.md）
- mptext API 当前免费，可能后续收费
