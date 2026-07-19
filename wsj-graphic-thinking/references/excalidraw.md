# Excalidraw 格式规范

## 格式优先级（按 Obsidian Excalidraw 插件版本自动选择）

| 优先级 | 格式 | 适用版本 |
|:------:|------|:--------:|
| 首选 | `.excalidraw.md` — ````json` 代码块 + `%%` | 当前插件 (≥2.0) |
| 备选 | `.excalidraw` — 纯 JSON | 所有版本通用 |
| 兼容 | `.excalidraw.md` — `## Drawing` + JSON + `%%` | 部分旧版本 |

## .excalidraw.md 格式（推荐）

```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW ... ⚠== ...


## Drawing

```json
{full-excalidraw-json}
```

%%
```

## .excalidraw 格式（通用）

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [...],
  "appState": { "viewBackgroundColor": "#ffffff" },
  "files": {}
}
```

> 必含 `files: {}` 字段，否则 Obsidian 识别为旧版格式。

## 保存路径

```
00-Attachments/Excalidraw/{YYYY-MM-DD}-{主题缩写}-{图形类型}.excalidraw.md
```

## 字体

| fontFamily | 字体 | 用途 |
|:----------:|------|------|
| 1 | Virgil（手绘体） | 默认，节点标题、箭头标签 |
| 2 | Helvetica（无衬线） | 副标题、注释、长文本 |
| 3 | Cascadia（等宽） | 代码/数据标注 |

## 字体层级

```
标题       fontSize 24, fontFamily 1, #1e1e1e
副标题     fontSize 16, fontFamily 1/2, #757575
节点标题   fontSize 18~22, fontFamily 1, textAlign center
节点副标题  fontSize 16, fontFamily 2, textAlign center
箭头标签   fontSize 16, fontFamily 1
脚注注释   fontSize 14, fontFamily 2
洞察文本   fontSize 16, fontFamily 2, #495057
```

## 容器绑定

所有形状内的文字必须使用：
```json
{"boundElements": [{"id": "text_id", "type": "text"}]}
{"containerId": "shape_id", "originalText": "...", "autoResize": true}
```
禁止使用 `label` 字段。
