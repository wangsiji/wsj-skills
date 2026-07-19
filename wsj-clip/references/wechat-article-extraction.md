# 微信公众号文章提取

当需要剪藏微信公众号文章（`mp.weixin.qq.com/s/...`）时，VNC CDP 方案可能遇到 CAPTCHA。替代方案：curl + 移动端 UA 直接获取 HTML，Python 提取。

## 核心流程

### 1. 下载全文（移动端 UA 绕过反爬）

```bash
curl -sL -A "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36" \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" -o /tmp/wechat.html
```

### 2. 检测页面类型 + 提取

**⚠️ 必须先检测页面类型再提取**，两种格式的解析路径完全不同。分享页的 `<meta name="author">` 永远返回空字符串，必须用 `nick_name`。

```python
import re, html

with open("/tmp/wechat.html", encoding="utf-8") as f:
    content = f.read()

# === 页面类型检测 ===
has_js_content = 'id="js_content"' in content       # 标准文章页
has_share_page = 'share_content_page' in content     # 分享页
has_captcha = 'captcha' in content.lower() or '验证' in content

# === 通用作者提取（先试试 nick_name，两种页面都可用） ===
author = "Unknown"
for m in re.finditer(r'nick_name\s*[:=]\s*["\x27]([^"\x27]+)', content):
    val = m.group(1)
    if val and val not in ('', '微信广告'):
        author = html.unescape(val)
        break

if has_captcha:
    # ⚠️ CAPTCHA 触发但内容可能仍在 content_noencode 中可用
    # 不要直接返回空 — 先尝试 content_noencode 兜底提取
    _captcha_content = ""
    for _m in [re.search(r"content_noencode:\s*'([^']+)'", content),
               re.search(r'content_noencode:\s*"([^"]+)"', content)]:
        if _m:
            _captcha_content = _m.group(1)
            break
    if _captcha_content:
        title = "Unknown (CAPTCHA)"
        # 尝试找标题
        for _tm in [re.search(r"msg_title\s*=\s*'([^']+)'", content),
                    re.search(r"window\.title\s*=\s*'([^']+)'", content),
                    re.search(r'og:title[^>]*content="([^"]+)"', content)]:
            if _tm:
                title = html.unescape(_tm.group(1))
                break
        body = _captcha_content
        body = body.replace('\\x22', '"').replace('\\x0a', '\n').replace('\\n', '\n')
        body = body.replace("\\'", "'").replace('\\x26', '&').replace('\\x3c', '<').replace('\\x3e', '>').replace('\\t', '  ')
        body = html.unescape(body)
        body = re.sub(r'\n{4,}', '\n\n', body)
    else:
        title = "Unknown"
        body = "CAPTCHA — 无备用内容源"
elif has_js_content:
    # === 标准文章页 ===
    m = re.search(r"msg_title\s*=\s*'([^']+)'", content)
    title = html.unescape(m.group(1)) if m else "Unknown"
    if author == "Unknown":
        m = re.search(r'nickname\s*=\s*"([^"]+)"', content)
        author = html.unescape(m.group(1)) if m else "Unknown"
    # 正文提取...
    m = re.search(r'id="js_content"[^>]*style="[^"]*"[^>]*>(.*?)</div>\s*(?:<script|<div)', content, re.DOTALL)
    if m:
        raw = m.group(1)
        # 转文本 — 保留基本格式
        raw = re.sub(r'<br\s*/?>', '\n', raw)
        raw = re.sub(r'</p>', '\n\n', raw)
        raw = re.sub(r'</h[1-4]>', '\n\n', raw)
        raw = re.sub(r'<h([1-4])[^>]*>', lambda m: '#' * int(m.group(1)) + ' ', raw)
        raw = re.sub(r'<strong[^>]*>', '**', raw)
        raw = re.sub(r'</strong>', '**', raw)
        raw = re.sub(r'<em[^>]*>', '*', raw)
        raw = re.sub(r'</em>', '*', raw)
        raw = re.sub(r'<img[^>]*data-src="([^"]+)"[^>]*>', r'\n![图片](\1)\n', raw)
        raw = re.sub(r'<pre[^>]*>', '\n```\n', raw)
        raw = re.sub(r'</pre>', '\n```\n', raw)
        raw = re.sub(r'<code[^>]*>', '`', raw)
        raw = re.sub(r'</code>', '`', raw)
        raw = re.sub(r'<li[^>]*>', '- ', raw)
        raw = re.sub(r'</li>', '', raw)
        raw = re.sub(r'<section[^>]*>', '', raw)
        raw = re.sub(r'</section>', '', raw)
        raw = re.sub(r'<span[^>]*>', '', raw)
        raw = re.sub(r'</span>', '', raw)
        raw = re.sub(r'<[^>]+>', '', raw)
        raw = html.unescape(raw)
        raw = re.sub(r'\n{4,}', '\n\n', raw)
        lines = [l.rstrip() for l in raw.split('\n')]
        body = '\n'.join(lines).strip()
    else:
        body = "提取失败"

elif has_share_page:
    # === 分享页格式 ===
    m = re.search(r"window\.title\s*=\s*'([^']+)'", content)
    title = html.unescape(m.group(1)) if m else "Unknown"
    m = re.search(r"content_noencode:\s*'([^']+)'", content)
    if not m:
        m = re.search(r'content_noencode:\s*"([^"]+)"', content)
    if m:
        body = m.group(1)
        body = body.replace('\\x22', '"').replace('\\x0a', '\n')
        body = body.replace('\\x26', '&').replace('\\x3c', '<').replace('\\x3e', '>')
        body = body.replace('\\n', '\n').replace("\\'", "'").replace('\\t', '  ')
        body = html.unescape(body)
        body = re.sub(r'\n{4,}', '\n\n', body)
    else:
        body = "提取失败"
else:
    title, body = "Unknown", "提取失败 — 未知页面类型"

print(f"PAGE_TYPE: js_content={has_js_content} share_page={has_share_page} captcha={has_captcha}")
print(f"TITLE: {title} | AUTHOR: {author} | BODY: {len(body)} chars")

with open("/tmp/wechat_body.txt", "w", encoding="utf-8") as f:
    f.write(body)
with open("/tmp/wechat_meta.txt", "w", encoding="utf-8") as f:
    f.write(f"TITLE:{title}\nAUTHOR:{author}\n")
```

## 字段位置

| 字段 | HTML 中位置 | 引号 | 说明 |
|------|------------|------|------|
| 标题 | `var msg_title = '...'` | **单引号** | JS 变量赋值 |
| 作者 | `nickname="林月半子的AI笔记"` | **双引号 ⚠️** | 公众号名称，绑定在 HTML attribute 上 |
| 正文 | `<div id="js_content">...</div>` | — | 富文本 HTML，含图片、加粗、标题 |
| 描述 | `var msg_desc = '...'` | 单引号 | 摘要/描述 |
| 原文链接 | `var msg_link = '...'` | 单引号 | 文章永久链接 |

## ⚠️ 已知陷阱

### 1. nickname 用双引号，不是单引号

老代码：`r"nickname\s*=\s*'([^']+)'"` → ❌ 永远抓不到
正确：`r'nickname\s*=\s*"([^"]+)"'` → ✅ 抓到"林月半子的AI笔记"

因为 `nickname` 是 HTML attribute（`nickname="xxx"`），不是 JS 变量。

### 2. 代码块内的 `#` 注释不是 H1

合并时去重 H1 的正则（`re.sub(r'^#\s.+?$\n?', '', body)`）会误删代码块里的 bash 注释。正确做法是只清除非代码块内 H1，或者降级时只针对代码块外。

### 3. 图片用 data-src 不是 src

微信文章图片 CDN 地址在 `data-src` 属性，不是 `src`。替换时用：
```
r'<img[^>]*data-src="([^"]+)"[^>]*>'
```

### 4. 作者提取：`nick_name` 是两种页面类型的通用 fallback

标准页用 `nickname="xxx"`（HTML attribute），分享页用 `nick_name: 'xxx'`（JS 数据）。但实践中：
- 分享页 `<meta name="author">` 永远为空 → 必须用 `nick_name`
- 标准页的 `nickname` attribute 在某些布局中也可能缺失 → `nick_name` 可作为兜底

**推荐顺序**：先扫 HTML 中所有 `nick_name` 出现（两个页面类型都有），找不到再降级到类型特定方法。代码：
```python
for m in re.finditer(r'nick_name\s*[:=]\s*["\x27]([^"\x27]+)', content):
    val = m.group(1)
    if val and val not in ('', '微信广告'):
        author = html.unescape(val)
        break
```

### 5. 页面类型检测必须在提取之前

直接用标准页提取方法处理分享页会返回空正文/空作者。必须先检测：
```python
has_js_content = 'id="js_content"' in content       # 标准页
has_share_page = 'share_content_page' in content     # 分享页
```

## 与 getnote 合并

body 和 getnote AI 总结都拿到后，合并写入 Raw/：

```python
# body 去重复 H1（注意不要碰代码块内的 #）
body_clean = re.sub(r'^#\s.+?$\\n?', '', raw_body, count=0, flags=re.MULTILINE).strip()

merged = f"{fm}\\n\\n# {title}\\n\\n## AI 智能总结\\n\\n{ai_summary}\\n\\n## 剪藏原文\\n\\n{body_clean}\\n"

# 降级 剪藏原文 下的标题
parts = merged.split("## 剪藏原文", 1)
if len(parts) == 2:
    clip_body = parts[1]
    clip_body_demoted = re.sub(r'^(#+) ', lambda m: "#" + m.group(1) + " ", clip_body, flags=re.MULTILINE)
    clip_body_demoted = re.sub(r'^# (?!#)', "## ", clip_body_demoted, flags=re.MULTILINE)
    merged = parts[0] + "## 剪藏原文" + clip_body_demoted
```

## 注意事项

- **移动端 UA 是关键**：桌面 UA 会被微信反爬拦截，返回"环境异常"CAPTCHA
- **图片链接保留**：`data-src` 存入 markdown，实际加载需手动下载
- **付费文章**：仍需要微信登录态，curl 无法抓取
- **与 vnc-clip.py 的关系**：普通的微信文章用此方案（更快更稳），需登录才能看的付费文章才需要 VNC CDP
- **文件编码**：HTML 用 utf-8 读取，否则中文乱码

## 特殊布局：微信分享页（share_content_page）

部分微信链接是**分享页格式**，而非标准 `mp.weixin.qq.com/s/...` 文章页：

### 特征
- HTML 中无 `id="js_content"` 富文本正文
- HTML 中无 `nickname="xxx"` 属性（nickname 为空）
- 页面显示"轻触阅读原文"按钮，点击才展开
- curl + 移动端 UA **和** CDP 浏览器都可能触发 CAPTCHA
- 核心内容在 JS 变量中，可以直接提取

### 提取方法

```python
import re, html

# 标题 — 标准 msg_title 格式不可用，用 window.title
m = re.search(r"window\.title\s*=\s*'([^']+)'", content)
title = html.unescape(m.group(1)) if m else "Unknown"

# 作者 — ⚠️ 不要用 <meta name="author">（实际为空字符串！）
#     正确来源：JS 数据中的 nick_name 字段
m = re.search(r"nick_name:\s*'([^']+)'", content)
author = m.group(1) if m else "Unknown"

# 正文 — 从 content_noencode JS 变量提取
m = re.search(r"content_noencode:\s*'([^']+)'", content)
if m:
    body = m.group(1)
    # 完整的转义字符处理（微信分享页用 JS 字符串存储，含多层转义）
    body = body.replace('\\x22', '"')   # 双引号
    body = body.replace('\\x0a', '\n')  # 换行
    body = body.replace('\\x26', '&')   # & 符号
    body = body.replace('\\x3c', '<')   # 小于号
    body = body.replace('\\x3e', '>')   # 大于号
    body = body.replace('\\n', '\n')    # 另一种换行表示
    body = body.replace("\\'", "'")     # 单引号
    body = body.replace('\\t', '  ')    # 制表符
    body = html.unescape(body)         # HTML entities（&amp;等）
    body = re.sub(r'\n{4,}', '\n\n', body)
```

### 检测方法

提取前检查页面类型：
```python
has_js_content = 'id="js_content"' in content       # 标准文章页
has_share_page = 'share_content_page' in content     # 分享页
has_captcha = 'captcha' in content.lower() or '验证' in content
```

### ⚠️ 分享页已知陷阱

#### 1. `<meta name="author">` 为空，用 `nick_name`

分享页中 `<meta name="author" content="">` 永远是空字符串，不要用它提取作者。
正确来源是 JS 数据中的 `nick_name` 字段：
```
nick_name: 'AI心意流动',
```
用正则 `r"nick_name:\s*'([^']+)'"` 提取。

#### 2. content_noencode 含多层转义

微信分享页用 JS 字符串存储正文，转义层级比标准 JSON 多。需要处理的转义序列：
- `\x22` → `"`（双引号，最常见）
- `\x0a` → `\n`（换行）
- `\x26` → `&`（&符号）
- `\x3c` → `<`（小于号）
- `\x3e` → `>`（大于号）
- `\n` → `\n`（字面反斜杠+n）
- `\'` → `'`（单引号）
- `\t` → 空格（制表符）

处理顺序：先还原 `\x` 转义序列，再还原 `\n`/`\'` 等，最后 `html.unescape()` 处理 HTML entities。

#### 3. 分享页正文短（数百字 vs 标准页数千字）

分享页只包含预览摘要，非全文。如需全文需点击"阅读原文"访问标准文章页。
