---
name: kcv-carddata
description: cardData字段规范——图形知识卡片的输入格式。
---

## cardData 规范

```json
{
  "tag": "COGNITION",     // COGNITION/WEALTH/GROWTH/STRATEGY
  "number": "001",        // 3位数字
  "title": "标题",         // ≤8汉字
  "subtitle": "ENGLISH",  // 英文全大写
  "summary": "一句话概要",
  "mechanism": "机制解释（可选）",
  "actions": [
    {"step": "①", "title": "行动名", "desc": "描述"}
  ],
  "groups": [
    {"label": "A", "badge": "☉", "title": "标题", "desc": "描述", "color": "#b8a088"}
  ],
  "quote": "金句",
  "author": "作者名"
}
```

