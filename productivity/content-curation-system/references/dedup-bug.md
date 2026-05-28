# SQLite 去重查询 bug — 2026-05-12 实测

## 问题

推文每次运行都返回全部推文，不去重，数据库也没有记录增长。

## 根因

`conn.execute("SELECT...")` 返回 `cursor` 对象，cursor 对象在 `if` 判断里永远为 truthy（即使查询结果为空）。

```python
# ❌ 错误写法
if conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id=?"):
    continue  # 永远执行到这里，因为 cursor 是 truthy
conn.execute("INSERT INTO seen_tweets ...")  # 永远插入

# ✅ 正确写法
if conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id=?").fetchone():
    continue  # 只有查到记录才跳过
conn.execute("INSERT INTO seen_tweets ...")  # 没查到才插入
```

## 症状对比

| 症状 | 错误写法 | 正确写法 |
|------|---------|---------|
| 第二次运行 | 返回全部推文 | 只返回新增推文 |
| 数据库记录 | 不增长 | 每次增长 |
| 调试 | cursor 对象永远 truthy | fetchone() 返回 None 或 tuple |

## 修复

所有 SQLite 去重查询都要 `.fetchone()`：

```python
# 查重
if conn.execute("SELECT 1 FROM seen_tweets WHERE tweet_id=?", (tweet_id,)).fetchone():
    continue

# 插入
conn.execute("INSERT INTO seen_tweets (tweet_id, handle) VALUES (?, ?)", (tweet_id, handle))
```

## 影响范围

- `daily-digest.py`（已修复）
- `twitter-fetch.py`（早期版本，如有使用需检查）
- `wechat-fetch.py`（待接入，需注意）
