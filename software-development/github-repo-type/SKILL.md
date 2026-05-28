---
name: github-repo-type
description: 快速判断一个 GitHub 仓库应该怎么安装/集成到 Hermes——是 Hermes skill、CLI 工具、还是 MCP server。避免把独立项目误当成 Hermes skill 安装。
version: 1.0.0
author: Hermes Agent
tags: [hermes, skills, mcp, github, installation]
---

# GitHub 仓库类型判断

## 四种类型

| 类型 | 安装方式 | 判断依据 |
|------|---------|---------|
| **Hermes Skill** | `hermes skills install <id>` | 仓库里有 `SKILL.md`，且 frontmatter 是 Hermes 格式（name/description/category 字段） |
| **Claude Code Skill** | `git clone` + `./install.sh`（或 pip install） | 仓库里有 `SKILL.md`，但 frontmatter 含 `user-invocable: true` 字段，且常有 `main.py` + `scripts/` 目录 |
| **CLI 工具** | `git clone` + `pip install` / `pip install -e .` | 有 `pyproject.toml`/`setup.py`，但没有 `SKILL.md` |
| **MCP Server** | `git clone` + 配置到 `config.yaml` 的 `mcp` 段落 | 仓库名含 `mcp`，或 README 描述为"MCP server" |

## 判断流程

1. 打开 GitHub 仓库首页
2. 看根目录有没有 **`SKILL.md`** → 读 frontmatter：Hermes 格式还是 Claude Code 格式（`user-invocable: true` 即为 Claude Code Skill）
3. 看有没有 **`pyproject.toml`** 或 **`setup.py`** → CLI 工具
4. 看 README 是否描述为 **"MCP server"** 或仓库名含 `mcp` → MCP server
5. 以上都没有 → 可能是普通代码库，需要手动分析

## 实际操作命令

### 安装 Claude Code Skill

```bash
git clone https://github.com/用户名/仓库名.git
cd 仓库名
# 先建 venv（Debian 系统 Python 是 externally-managed，必须用 venv）
python3 -m venv venv
source venv/bin/activate
# 然后按项目说明安装（通常有 install.sh）
pip install -r requirements.txt
playwright install chromium  # 如需浏览器自动化
```

注意：Claude Code Skill 的 SKILL.md 不能直接给 Hermes 用（frontmatter 格式不同）。可以在 Hermes 里通过 `terminal` 工具调用其 `main.py`。

### 安装复合型项目（子仓库模式）

部分 Claude Code Skill 在 `install.sh` 里嵌套克隆了 MCP 子仓库（如 `wexin-read-mcp`、`feishu-read-mcp` 等）。安装这类项目时注意：

```bash
git clone https://github.com/用户名/仓库名.git
cd 仓库名
python3 -m venv venv
source venv/bin/activate
# install.sh 会自动克隆子仓库并 pip install
bash install.sh
```

如果 `install.sh` 因为 `pip` 的 `externally-managed-environment` 报错：
```bash
# 不要加 --break-system-packages，而是手动分步：
source venv/bin/activate
pip install -r requirements.txt          # 主依赖
pip install -r wexin-read-mcp/requirements.txt  # 子仓库依赖（如果有）
playwright install chromium              # 浏览器自动化（~288MB）
```

Playwright 的 Chromium 下载 ~288MB（Chrome for Testing ~175MB + Headless Shell ~113MB），存放在 `~/.cache/ms-playwright/`。如果 VPS 磁盘空间有限，提前确认。

### 安装 CLI 工具
```bash
git clone https://github.com/用户名/仓库名.git
cd 仓库名
pip install -e .   # 开发模式
# 或
pip install .       # 生产模式
```

### 安装 MCP Server
```bash
git clone https://github.com/用户名/仓库名.git
# 然后用 hermes mcp add 配置
hermes mcp add <name> --command "python" --args "path/to/server.py"
```

### 安装 Hermes Skill
```bash
hermes skills install <skill-id>
# 或从 GitHub 安装（如果支持）
hermes skills tap add https://github.com/用户名/仓库名
```

## 常见误区

- ❌ 以为所有好东西都能 `hermes skills install`
- ❌ 以为 GitHub 项目都有 `SKILL.md`
- ❌ 混淆"MCP server"和"Hermes skill"——两者完全不同
- ❌ 把 Claude Code Skill 当 Hermes Skill 装（frontmatter 格式不同，装不上）

## 坑：浏览器认证在无头服务器上

许多 Claude Code Skill（如 NotebookLM 相关工具、xurl 的 OAuth 等）需要打开浏览器完成 Google/X OAuth 认证。VPS 无显示器环境会直接报错：

```
Error: BrowserType.launch_persistent_context: Missing X server or $DISPLAY
```

**处理方式：**

```bash
# 方案 A：xvfb-run 提供虚拟显示器
xvfb-run notebooklm login
# 仍需要用户交互（输账号密码），超时 30s 是常见现象

# 方案 B：本机登录后传凭证到服务器
# 在自己电脑上跑 notebooklm login → scp ~/.notebooklm/ 到服务器

# 方案 C：环境变量注入
export NOTEBOOKLM_AUTH_JSON='{"cookie": "..."}'
# 或通过 notebooklm-py 文档说的 NOTEBOOKLM_AUTH_JSON 路径方式
```

如果方案 A 也超时，通常是 Google 服务在大陆网络不通（即使 VPS 在海外，部分机房 IP 也被标记为 unsupported）。此时工具的核心依赖（NotebookLM 上传）不可用，需要优先解决网络问题或换方案。

## 快速验证

安装完后，确认是否成功：
```bash
# CLI 工具
<命令名> --help

# MCP server
hermes mcp list

# Hermes skill
hermes skills list
```

## 关键判断问题

遇到用户想安装 GitHub 上的项目时，先问自己：
1. 仓库有 `SKILL.md` 吗？
   - Hermes 格式（name/description/category）→ Hermes Skill
   - Claude Code 格式（user-invocable: true）→ Claude Code Skill
2. 仓库是 `mcp` 相关吗？→ MCP server
3. 仓库有 `pyproject.toml` 吗？→ CLI 工具
4. 都不符合 → 普通代码，需要单独分析
