---
name: kcv-deployment
description: 图形卡片部署方法——生成→写入→sudo cp到公开目录→验证。
---

## 部署方法（关键）

```python
from hermes_tools import write_file, terminal

# 1. 构建完整 HTML
html = f'''<!DOCTYPE html>...'''

# 2. 写入临时文件
write_file(path="/tmp/card.html", content=html)

# 3. sudo cp 到公开目录
r = terminal("sudo cp /tmp/card.html /var/www/knowledge-cards/{title}.html && sudo chmod 644 /var/www/knowledge-cards/{title}.html")
```

> ⚠️ `/var/www/knowledge-cards/` 属 root 所有，`write_file` 无法直接写入。必须两段式。
> ⚠️ 不要用 `sed` 或 `patch` 填充模板 — 一次性用 `execute_code` 完整写出。


## 验证

生成后用 `browser_navigate` 打开链接确认渲染效果。截图给用户确认后结束。

