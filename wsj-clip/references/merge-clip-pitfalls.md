---
name: clip-merge-pitfalls
description: merge-clip.py 已知坑（已实测修复，沉淀防回归）。调用前必读。
---

# merge-clip.py 已知坑（已实测修复，沉淀防回归）

- **参数数量**：脚本 `len(sys.argv)` 校验必须是 `!= 7`（argv[1..6] = type+title+author+url+body+ai_summary）。早期误写 `!= 6` 会拒绝合法调用。
- **参数顺序**：`argv[5]` = body_file，`argv[6]` = ai_summary_file。调脚本时 **body 在前、ai_summary 在后**，反了内容错位。
- **重复 H2 标题**：若传给 ai_summary 的内容自带 `## AI 智能总结` 标题，合并后会叠出双标题。传前先去掉 ai_summary 首行 H2，或合并后用 `patch` 删重复行。
- **无效正则**：截断公众号 `往期回顾` 用 `re.sub(r'\n往期回顾.*$', '', body, flags=re.DOTALL)`。不要用 `\n****` 这类转义（部分 Python 版本抛 `bad escape` 异常，直接中断合并）。
- **GitHub README 大小陷阱**：抓 raw README 后先检查大小。`< 30KB` 全文存（放 `## 完整 README` 段）；`≥ 30KB` 只抽核心段（简介/特性/安装/用法）截到 ~20KB 内，注明"README 全文 XXX KB 为 manpage 选项参考，已节选"。截断法：抓 `简介段 + INSTALLATION 段`（到第一个 `## <大写选项>` 之前），跳过尾部选项字典。
