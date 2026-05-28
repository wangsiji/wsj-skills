---
name: obsidian
description: Read, search, and create notes in the Obsidian vault.
---

## Knowledge Cards（知识卡片）

知识卡片目录：`/home/wangsiji/projects/knowledge/cards/`

知识卡片由 `knowledge-card` skill 生成，格式为常青笔记（Evergreen Notes），与 llm-wiki 是两种互补模式：

| 模式 | 触发场景 | 目录 |
|------|----------|------|
| **知识卡片** | 读完书/播客后提取卡片 | `/home/wangsiji/projects/knowledge/cards/` |
| **llm-wiki** | 深入研究一个主题 | `_wiki/` |

两者都放在同一个 Obsidian vault 下，不需要重建结构。**不要因为想用 llm-wiki 就重建已有的 Obsidian 结构。**

---

## Obsidian Vault

**Location:** `/home/wangsiji/projects/wsj-second-brain`

> 用户 vault 路径已固定，不在默认的 `$HOME/Documents/Obsidian Vault`。

**人生主线结构（固定）：**
- 健康 > 生活 > 价值
- 健康子主线：运动、饮食、睡眠、情绪
- 生活子主线：家庭生活、人际社群、体验突破、休闲娱乐
- 价值子主线：财务理财、工作事业、学习成长

> 注意：体重不是独立子主线，属于运动/饮食。所有 OKR/规划/整理基于上述固定结构。

## Read a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat "$VAULT/Note Name.md"
```

## List notes

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# All notes
find "$VAULT" -name "*.md" -type f

# In a specific folder
ls "$VAULT/Subfolder/"
```

## Search

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# By filename
find "$VAULT" -name "*.md" -iname "*keyword*"

# By content
grep -rli "keyword" "$VAULT" --include="*.md"
```

## Create a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

## Append to a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "
New content here." >> "$VAULT/Existing Note.md"
```

## Cross-Device Sync（跨设备同步）

### ✅ 跨平台同步方案

**结论：iCloud Drive 在 Linux 上无法挂载。** Apple 没有公开 WebDAV 接口，`icloud.com/icloud-drive` 是 404，davfs2 / pyiCloud / rclone 全部走不通 iCloud 私有 CloudKit 协议。

**推荐方案：Syncthing（真正的三端双向同步）**

```
iPhone ↔ Mac ↔ VPS（Syncthing P2P 网络）
        同一文件夹，任何端改动，其他端秒级同步
```

**已在 VPS 上部署 Syncthing：**
- 设备 ID：`XTMLFNH-LYUQY2I-XERNZRV-MOYENQA-PTTAM5X-O56DP5F-WSHVBWF-5WMC2AA`
- GUI 端口：8384（已监听公网）
- 数据端口：22000（TCP/QUIC）
- 二进制：`/usr/local/bin/syncthing`（v2.0.16）
- 配置目录：`/var/syncthing/`
- API Key：`m4HTqYUfEetb7gMjJk7nmeKzhe7Qq9fa`
- 同步文件夹位置：`/home/wangsiji/projects/wsj-second-brain`

**三端配置：**
1. Mac：安装 Syncthing，添加 VPS 设备 ID，共享文件夹指向 Obsidian 仓库
2. iPhone：App Store 安装 Syncthing，同上
3. VPS：已就绪，无需额外配置

**管理界面**：`http://192.3.16.123:8384`（设备 ID 已预配置，首次访问设密码）

**备选方案：Git 中转**
```
Mac (Obsidian, iCloud) → GitHub → VPS (cron pull)
                              ↘ iPhone (Working Copy)
```
- Mac 上 Obsidian 仓库配 Git，每次编辑自动 push
- VPS 定时 `git pull`
- 适合不想在 Mac 跑 Syncthing 常驻进程的场景

### 快速上手 Git 中转

Mac Obsidian 仓库路径：
```
~/Library/Mobile Documents/iCloud Documents/Obsidian/Documents/<仓库名>/
```

在 Mac 终端初始化 Git（只需一次）：
```bash
cd ~/Library/Mobile\ Documents/iCloud\ Documents/Obsidian/Documents/你的仓库名
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

Mac 上装 Obsidian Git 插件（自动 push）或每次手动 `git push`。

服务器定时拉取：
```bash
*/15 * * * * cd ~/你的仓库路径 && git pull --rebase >> ~/.obsidian_sync.log 2>&1
```

### 环境变量配置

```bash
# ~/.bashrc 或 ~/.zshrc
export OBSIDIAN_VAULT_PATH="$HOME/Documents/Obsidian Vault"
```

---

## LLM Wiki（知识积累系统）

用户使用 Obsidian 作为长期知识库，基于 Karpathy 的 LLM Wiki 模式。`_wiki/` 文件夹嵌入在 vault 内。

### 目录结构

```
vault/
├── _wiki/
│   ├── index.md              ← 目录，所有页面的清单
│   ├── log.md                ← 日志，每次操作记录
│   ├── raw/articles/         ← Layer 1：原始资料（不可改）
│   ├── concepts/             ← Layer 2：概念/主题页
│   ├── entities/             ← Layer 2：人物/地点/事件页
│   └── comparisons/         ← Layer 2：对比分析页
└── [vault其他内容]
```

**三层规则：**
- `raw/` — 原始资料，只增不改，保存每次摄入的源内容
- `concepts/` `entities/` `comparisons/` — 消化后的 wiki 页面，可修改、可链接
- `index.md` `log.md` — 导航，每次操作必须更新

### 完整工作流

**第一步：存原始资料**
```bash
vault/_wiki/raw/articles/<源名-日期>.md
```
文件开头加 frontmatter：
```yaml
---
source_url: <来源URL>
ingested: YYYY-MM-DD
---
```

**第二步：写 wiki 页面**
- `concepts/` — 概念/主题页
- `entities/` — 人物/地点/组织页
- 每个页面必须有 `[[wikilinks]]` 链接到至少2个其他页面

页面 frontmatter：
```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | entity | comparison
tags: [标签1, 标签2]
sources: [_wiki/raw/articles/源文件.md]
confidence: high | medium | low
---
```

**第三步：更新索引和日志**
- `index.md`：添加新页面
- `log.md`：记录本次操作

### 用户的使用习惯

- 不建复杂分类，不打很多标签
- 从一个具体的点开始（比如「腾冲历史」），然后横向扩展
- 看完一个电视剧/书/纪录片，就地写一页
- 与已有 Obsidian 笔记互链（不重复造轮子）

### wiki 页面模板

```markdown
---
title: 标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | entity | comparison
tags: [标签]
sources: [_wiki/raw/articles/源.md]
confidence: medium
---

# 标题

## 核心要点
（一句话说明这是什么）

## 详细内容

## 相关页面
- [[相关页面1]]
- [[相关页面2]]

## 参考
- [来源链接](url)
```

---

## Web Clipping（网页剪藏）

VPS 上向 Obsidian vault 剪藏网页内容的两种方案。

### 方案A：noVNC 桌面 + Chrome Web Clipper 扩展

适合需要登录的页面（Twitter/X、需要 cookie 的站点）。

```bash
# 1. 确保 noVNC 桌面运行（详见 vps-remote-desktop skill）
# 2. 启动 Chrome（Web Clipper 扩展位于 /tmp/obsidian-clipper/dist）
DISPLAY=:2 google-chrome-stable --no-sandbox --load-extension=/tmp/obsidian-clipper/dist

# 3. 浏览器访问 http://192.3.16.123:6080/vnc.html
#    VNC 密码: test1234
#    在桌面 Chrome 里打开目标页面，点扩展图标剪藏
```

Vault 内已安装 `obsidian-local-rest-api` 插件，Web Clipper 扩展可通过 localhost API 写入 vault。

### 方案B：CLI 脚本 `scripts/clip.py`

适合无需登录的普通网页，可集成 cron 自动化。

```bash
python3 scripts/clip.py <url>                          # → 默认 Clippings/
python3 scripts/clip.py <url> --dir "_wiki/raw/articles"  # → 指定目录
python3 scripts/clip.py <url> --stdout                  # 只输出，不保存
```

**原理**：Chrome headless `--dump-dom` → bs4 智能定位文章主体 → markdownify 转 markdown → frontmatter + 内容写入 vault。

**依赖**：`python3-bs4`、`markdownify`（已预装）。

### X/Twitter 文章剪藏

X Articles（长文）和部分推文需要登录态 + JS 渲染才能获取内容，`clip.py`（方案B）无法直接处理。两种方式：

**方式一：Hermes 浏览器工具注入 cookie 提取文本**
```
# 1. 获取 cookie
cat ~/.config/xfetch/session.json
# 2. 浏览器注入（详见 references/x-article-clipping.md）
# 3. 提取正文 → 手动保存到 vault
```

**方式二：VNC 桌面 + Web Clipper 扩展**
1. 检查 xreach 认证：`xreach auth check`
2. 打开 VNC 桌面 Chrome，导航到 `https://x.com`
3. 注入 cookie（从 `~/.config/xfetch/session.json` 取 auth_token + ct0）
4. 打开目标页面，按 Ctrl+Shift+O 触发扩展保存

详见 `references/x-article-clipping.md`。

---

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
