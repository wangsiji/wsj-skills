# Info-Feed 信息输入系统 — 实现细节

项目路径: `/home/wangsiji/projects/info-feed/`

## Provider 列表

| Provider | 文件 | 可配置列表 | 依赖 |
|----------|------|-----------|------|
| twitter | `providers/twitter.py` | `ACCOUNTS` (当前9个) | xreach CLI + auth cookie |
| bilibili | `providers/bilibili.py` | `UP_LIST` (当前1个) | RSSHub 自建 (8280端口) |
| jike | `providers/jike.py` | `USERS` (当前空) | 即刻 API token |
| xiaoyuzhou | `providers/xiaoyuzhou.py` | `PODCASTS` (当前1个) | RSS feed / RSSHub |

## Twitter 监控账号（当前）

```python
ACCOUNTS = [
    "karpathy", "sama", "paulg", "naval", "dotey",
    "LufzzLiz", "Lonely__MH",
    "wangcc_ps",  # 用户自己的号
]
```

## B站 UP 主（当前）

```python
UP_LIST = [
    {"name": "门冬冬", "mid": "14097567"},
]
```

## 小宇宙播客（当前）

```python
PODCASTS = [
    {"name": "一人公司", "pid": "6480b91120ec3cbc460382cc"},
]
```

## 输出目录

```
~/projects/wsj-second-brain/Inbox/_wiki/raw/{source}/{date}.md
```

## Cron 调度

- info-feed-twitter: 每天 8:00 / 20:00 北京时区
- 脚本: `~/.hermes/scripts/run-feed-twitter.sh`
- Hermes cronjob 管理，非系统 crontab

## 扩展指南

1. 新建 `providers/<name>.py`
2. 实现 `class XxxProvider(BaseProvider)` 含 `name` + `fetch()`
3. 在类内定义可配置列表（用户直接在文件里增删账号/频道）
4. 自动注册，无需改 feed.py
