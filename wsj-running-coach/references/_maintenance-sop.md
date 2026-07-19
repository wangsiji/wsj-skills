# running-coach 结构规范速查

> 本文件为正文「Skill 结构规范」段的展开版，供维护时逐项核对。

## 拆分 SOP（大文件 → 决策主线 + references/）

1. **备份**：`cp SKILL.md SKILL.md.bak.$(date +%Y%m%d)`
2. **整段切分（Python）**：读全文 splitlines，按 `## ` 定位段边界，避免 read_file 行号污染。
3. **下沉判断**：纯工具/数据/API/代码块下沉 references/；决策分支/规则/模板留主文件。
4. **补 frontmatter**：每个新 reference 加 `name`/`description`。
5. **顶部文档导航**：表格列「文件/内容/何时读」。
6. **去重**：同主题多源只留权威版，删冗余。
7. **主文件指针**：每个下沉段改为「详见 `references/xxx.md`」一行。
8. **诊断**：frontmatter 有效 → 引用文件全存在 → 无明文密码 → 脚本路径 custom/ → 无孤儿文件。

## 常见错误（已踩坑）

- read_file 行号前缀 `N|` 直接写回破坏 YAML → 用 terminal Python open() 读写。
- 路径写错 `skills/productivity/...`（实际 custom/）、`Core/马拉松比赛.md`（实际 01-Projects/Routine/）。
- 明文密码内联 → 改环境变量。
- 同内容两个 reference 文件（OCR 同时在 tooling-details 和 screenshot-parsing）→ 合并去重。
