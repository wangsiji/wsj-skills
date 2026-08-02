# 笔记属性格式标准（剪藏 Raw/ 规范 v3）

> 2026-07-28 大更新：统一七字段、嵌套 tags、标题依次降级、图片外链、AI 总结走 getnote API。
> 与 vault 全局 Metadata Schema（name/description/category/tags/status 等）对齐，去 created/modified/url 旧字段。

## Frontmatter 七字段（必填，顺序固定）

```yaml
---
name: 文章标题
description: "一句话摘要（含来源作者+核心内容，便于检索）"
category:
  - "[[公众号]]"
author:
  - "[[作者名]]"
source: "https://原文链接"
tags: [剪藏/来源, 剪藏/主题1, 剪藏/主题2]
status: ToDo
---
```

### 字段说明

- `name` — 文章标题（纯文本，不含链接）
- `description` — 一句话摘要，便于 vault 内检索预览
- `category` — 来源类型，用 `[[双链]]` 包裹（公众号 / X / 小宇宙 / B站 / GitHub 等）
- `author` — 作者名，用 `[[双链]]` 包裹
- `source` — 原文链接（取代旧 `url` 字段）
- `tags` — **嵌套格式**，见下
- `status` — 剪藏消化状态，新建时固定 `ToDo`（消化/提炼进 Topics 后改 `Done`）

### ❌ 禁止字段

- `created` / `modified` — 删除（git 已记录时间，不重复存）
- `url` — 改为 `source`
- 任何额外字段（title / published 等）

## Tags 嵌套规范

格式：`剪藏/{维度}`，每个剪藏文章**只保留最关键的 3 个标签**。

```yaml
tags: [剪藏/公众号, 剪藏/Obsidian, 剪藏/知识管理]
```

- 第一段固定 `剪藏`（便于 vault 筛选所有剪藏）
- 之后按「来源 / 主题」组合，最多 3 个
- 例：
  - 公众号 Obsidian 文 → `[剪藏/公众号, 剪藏/Obsidian, 剪藏/知识管理]`
  - X 智能体文 → `[剪藏/X, 剪藏/智能体, 剪藏/AI工具]`
  - GitHub 项目 → `[剪藏/GitHub, 剪藏/开源, 剪藏/知识提取]`

## 文件名格式

```text
Raw/:  {标题}.md
```

- **只保留标题**，去掉 `{来源}_{作者}_` 前缀（避免同名冲突靠 source 字段区分，不靠文件名）
- 标题净化：去特殊字符，空格保留或变下划线，取前 80 字符
- 例：`如何使用obsidian搭建知识库.md`

## 标题层级规则（v3：依次降级，保留真实嵌套）

文件结构：

```text
# {标题}                                    (h1: 文件主标题)
## AI 智能总结                              (h2: 区块)
  #### getnote 返回的小节（原 ### 降为 ####）  (h4)
## 剪藏原文                                 (h2: 区块)
  ### 原文一级章节（源 h1 → ###）            (h3)
  #### 原文子节（源 h2 → ####）             (h4)
  ##### 原文更深层（源 h3 → #####）          (h5)
```

**映射公式**：源 HTML 的 `hN` → vault 的 `###` + (N-1) 级（即 h1→###、h2→####、h3→#####），保留真实 DOM 父子嵌套。
- `一、操作面板`（源 h1）→ `### 一、操作面板`
- `左上板块`（源 h2，在"一、操作面板"下）→ `#### 左上板块`
- 更深层类推

**长描述降级**：源 HTML 里被标成 `<h1>/<h2>` 但实为"小节导语长句"（>25 字或含句号/逗号）的，不当标题，降级为普通正文段落。

**图片链接**：保留 `mmbiz.qpic.cn` 外链（`![](https://mmbiz.qpic.cn/...)`），**不下载本地**（跨设备同步靠外链，避免 assets 膨胀）。

## 表格规则

每一张 markdown 表格的**表头行前必须有一个空行**（GFM 渲染要求）。脚本 `ensure_table_blank_before()` 会自动补齐，但手写/BeautifulSoup 转换后需确认。

## AI 智能总结（走 getnote API，非手写）

`## AI 智能总结` 段内容由 **getnote API** 生成（提交链接 → 轮询 → 取 detail.content），不要手写。getnote 返回的 content 自带 `###` 小节，放进 `## AI 智能总结` 下需降级为 `####`。

流程见 `references/getnote-api.md` + `references/down-mptext-api.md`（workflow-web 串联）。

## 标准产出示例

```markdown
---
name: 如何使用obsidian搭建知识库
description: "公众号「起什么好3211」实操文——用 Obsidian 从信息收集到知识关联搭建个人知识库"
category:
  - "[[公众号]]"
author:
  - "[[起什么好3211]]"
source: "https://mp.weixin.qq.com/s/XXXX"
tags: [剪藏/公众号, 剪藏/Obsidian, 剪藏/知识管理]
status: ToDo
---

# 如何使用obsidian搭建知识库

> 来源信任层级：L3（公众号「作者」，非一手信源；内容为经验分享，可实操验证）

## AI 智能总结

#### **🏆 Obsidian是什么？**
（getnote 返回的结构化内容，含表格）

## 剪藏原文

### 一、操作面板

obsidian（黑曜石）是一款 Markdown 格式的个人知识库...

#### 左上板块

Obsidian 左侧的文件管理区...
```
