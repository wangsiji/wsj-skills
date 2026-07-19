---
name: tooling-details
description: running-coach程序化调用细节：COROS API端点 + coros-mcp cron代码（精简）
---

# Tooling Details — running-coach

> 本文件只存 `SKILL.md` 的程序化调用**代码片段**。API 端点与陷阱详见 `coros-api.md`，OCR 解析见 `screenshot-parsing.md`，体重/体脂见 `body-composition.md`。

## coros-mcp 程序化调用代码（cron 环境）

```python
import sys
sys.path.insert(0, '/home/wangsiji/projects/coros-mcp')
from coros_api import login, get_activities
from datetime import datetime, timedelta
import os
EMAIL = os.environ["COROS_EMAIL"]
PASSWORD = os.environ["COROS_PWD"]
ok = login(EMAIL, PASSWORD, region="cn")
if ok:
    acts = get_activities(
        (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        datetime.now().strftime('%Y%m%d')
    )
```

**优先级（cron 上下文）：** 1. Playwright 脚本 → 2. 等5秒重试 → 3. coros-mcp 程序化 API → 4. 缓存兜底 → 5. 占位数据兜底

**cron 限制：** `coros-mcp auth` 是交互式 CLI（用 input()），不能在 cron 用，必须 Python 程序化调 API。
