# 笔记属性格式标准

## Frontmatter 规范

```yaml
---
category:
  - "[[X]]"
  - "[[小宇宙]]"
  - "[[B站]]"
  - "[[公众号]]"
author:
  - "[[@ai_xiaomu]]"
  - "[[三五环]]"
url: "https://x.com/ai_xiaomu/status/2055184114110943538"
tags: [剪藏]
created: 20260604
modified: 20260604
---
```

## 目录路由与格式选择

| 目标目录 | Frontmatter 风格 | 日期字段 | 文件名格式 |
|----------|-----------------|----------|-----------|
| `Raw/` | 剪藏标准 | `created` + `modified` | `{来源}_{作者}_{标题}.md` |
| `Info/` | 笔记标准 | `published` | `{YYYYMMDD}_{标题}.md` |

### Raw/ 格式（剪藏标准）

使用 `created` / `modified` 双字段：

```yaml
---
category:
  - "[[X]]"
author:
  - "[[@ai_xiaomu]]"
url: "..."
tags: [剪藏]
created: 20260604
modified: 20260604
---
```

### Info/ 格式（笔记标准）

使用 `published` 单字段：

```yaml
---
category:
  - "[[抖音]]"
author:
  - "[[归藏]]"
url: "..."
tags: [剪藏, 抖音视频]
published: 20260604
---
```

## 字段说明

### 通用字段

- `category` — 来源类型，用 `[[双链]]` 包裹
- `author` — 作者名，用 `[[双链]]` 包裹
- `url` — 原文链接
- `tags` — 内联数组，必须含 `剪藏` 再加来源标签

### 按目录选填

- `Raw/` 目录：`created` + `modified`（双日期）
- `Info/` 目录：`published`（单发布日期）

**禁止添加 title 或其他额外字段到 frontmatter**

## 文件名格式

```
Raw/:  {来源}_{作者}_{标题}.md
Info/: {YYYYMMDD}_{标题}.md
```

- 来源：X / 公众号 / 小宇宙 / B站
- 作者：与 frontmatter 中 author 的第一个值一致
- 标题：净化后的标题（去掉特殊字符，空格变下划线），取前60字符
- YYYYMMDD：发布日期

## 标题层级规则

文件结构：

```
# {标题}                                    (h1)
## AI 智能总结 / AI摘要                       (h2)
  ### AI 生成的内容按原有层级排列               (h3+)
## 剪藏原文 / 抖音语音转文字原文               (h2)
  ### 原始文章标题（原h2降级而来）              (h3)
  #### 原始子标题（原h3降级而来）              (h4)
```

剪藏原文下的所有标题必须降一级（加一个 #），避免与 AI 总结的标题级别冲突。
