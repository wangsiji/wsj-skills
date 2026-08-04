---
name: hermes-profile-isolation
description: "为家人/不同身份建隔离 Hermes profile：独立模型、记忆、技能与聊天通道。"
version: 1.0.0
author: siji
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, profile, 隔离, 多身份, 通道]
    category: custom
---

# Hermes Profile 隔离部署

## 目标
为另一个人（如家人）或另一个身份/账号建一个**完全隔离**的 Hermes 实例，与当前 `default` profile 互不干扰：独立的模型配置、API key、记忆（MEMORY/USER）、技能、cron、聊天通道。

## 何时用
- 给家人/同事建专属智能体（如老婆的公众号助手）
- 为不同业务身份分流（个人号 vs 公司号）
- 需要多套互不污染的记忆/技能体系

## 核心流程

### 1. 建空 profile（最隔离）
```bash
hermes profile create <name> --no-skills --no-alias \
  --description "一句话角色描述，供 kanban 路由"
```
- `--no-skills`：不继承任何现有 skill（含你的 wsj-* 系列），最干净
- 不加 `--clone` / `--clone-all`：不复制 config/.env/记忆 → 真隔离
- 建好后目录 `~/.hermes/profiles/<name>/` 自带 `skills/`(空) `memories/`(空) `config.yaml`(无) `.env`(空)

### 2. 生成命令前缀（关键：多 profile 命令语法）
⚠️ **`hermes <profile> <command>` 会直接报错**（`invalid choice: '<profile>'`）。正确机制：
- `hermes profile use <name>` 切换 sticky default（**会改你的默认 profile**，仅临时配时慎用）
- **或**建 alias 包装脚本（推荐，不改 default）：
  ```bash
  hermes profile alias <name> --name <name>
  ```
  生成 `/home/wangsiji/.local/bin/<name>`，内容 `exec hermes -p <name> "$@"`
- 之后 `qiqiu setup` / `qiqiu config set ...` / `qiqiu chat` 全部作用于该 profile，且**不影响你的 default**

### 3. 配模型（非交互环境）
`qiqiu setup` 在管道/无 TTY 下走 non-interactive 模式**不写盘**。改用：
```bash
qiqiu config set model.default glm-4.7-flash
qiqiu config set model.provider zai
qiqiu config set model.base_url https://open.bigmodel.cn/api/paas/v4
```
- 验证写盘：`qiqiu config set model.default x` 写入 `~/.hermes/profiles/qiqiu/config.yaml`（非你的 default）
- API key：镜像进 `profiles/<name>/.env`（chmod 600）。例：`printf 'GLM_API_KEY=%s\n' "$KEY" > profiles/<name>/.env`
- ⚠️ `.env` 的 key 常带行尾注释（`sk-xxx  # 注释`），用 `cut -d= -f2- | sed 's/#.*//' | tr -d ' '` 剥离，否则值带注释 → 401 误判 key 失效

### 4. 配独立聊天通道
Hermes 支持微信通道，通过 `WEIXIN_*` 环境变量接入 iLinkAI 微信网关
（`WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com`，这是官方支持的类企业微信通道，
非 gewechat/wechaty 第三方桥接）。`WEIXIN_HOME_CHANNEL` 即该 profile 的微信会话标识
（形如 `o9cq802eLpEyLdDN-Ko6BfX3G3PQ@im.wechat`）。
- 微信：把 `WEIXIN_TOKEN` / `WEIXIN_BASE_URL` / `WEIXIN_CDN_BASE_URL` / `WEIXIN_DM_POLICY`
  / `WEIXIN_ALLOW_ALL_USERS` / `WEIXIN_ALLOWED_USERS` / `WEIXIN_GROUP_POLICY`
  / `WEIXIN_HOME_CHANNEL` 写进 `profiles/<name>/.env`，然后 `<name> gateway run` 启动。
  终端渲染二维码可能失败（No module named 'qrcode'），直接用输出的二维码**链接**打开扫码。
- Telegram（独立 bot）：第二个 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_USERS` 写进
  `profiles/<name>/.env`，`<name> gateway start` 独立端口。
- 企业微信：官方 API，需 corpid/secret。

### 4b. 跨 profile 的 cron 投递到家人微信（关键坑）
cron 任务运行在 **default 上下文**，投递时读的是 **default 的 `.env`** 里的通道配置，
**不是目标 profile 的**。所以要让 cron 把消息推到 `qiqiu` 的微信，必须把 `qiqiu` 的
整套 `WEIXIN_*` 配置（含 `WEIXIN_ACCOUNT_ID`）**镜像进 default 的 `.env`**：
```bash
cp ~/.hermes/.env ~/.hermes/.env.bak.$(date +%Y%m%d_%H%M)
cat >> ~/.hermes/.env << 'EOF'

# qiuqiu 微信通道(供 cron 投递用, 与 qiuqiu profile 共享同一 bot)
WEIXIN_TOKEN=<qiqiu的WEIXIN_TOKEN>
WEIXIN_ACCOUNT_ID=<qiqiu的WEIXIN_ACCOUNT_ID 即 token 前缀@im.bot>
WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com
WEIXIN_CDN_BASE_URL=https://novac2c.cdn.weixin.qq.com/c2c
WEIXIN_DM_POLICY=pairing
WEIXIN_ALLOW_ALL_USERS=false
WEIXIN_ALLOWED_USERS=
WEIXIN_GROUP_POLICY=disabled
WEIXIN_GROUP_ALLOWED_USERS=
WEIXIN_HOME_CHANNEL=<qiqiu的WEIXIN_HOME_CHANNEL>
EOF
```
cron 的 `deliver` 设为 `weixin:<WEIXIN_HOME_CHANNEL>`（如
`weixin:o9cq802eLpEyLdDN-Ko6BfX3G3PQ@im.wechat`）。
- ⚠️ 投递报 `platform 'weixin' not configured/enabled` → default `.env` 缺 `WEIXIN_*`。
- ⚠️ 投递报 `Weixin account ID missing` → 缺 `WEIXIN_ACCOUNT_ID`（取 `WEIXIN_TOKEN` 的
  `@im.bot` 前缀那段，如 `2985f9f09d7d@im.bot`）。
- ⚠️ 隔离性小妥协：default 因此也能发同一个微信 bot，但只是"能发"，无数据/记忆污染。
- 验证：`cronjob action=run` 后看 `last_delivery_error` 是否为 `null`。

### 4c. 从 Mac 迁来的 skill 改 Linux 路径（如 technical-monitor）
Mac 上写死的路径在 Linux 跑不了，需改 3 处并保留环境变量兜底：
- `NODE_BIN` 默认 → `/usr/bin/node`（先 `which node` 确认）
- 数据源脚本（如 westock-data 的 `index.js`）→ 放到 Linux 固定目录
  （如 `/home/wangsiji/.local/westock/scripts/index.js`），用 `WESTOCK_INDEX` 环境变量兜底
- 输出目录 `MONITOR_OUT_DIR` → Linux 的 vault 实际路径
  （如 `/home/wangsiji/projects/wsj-second-brain/03-Resources/Notes`），删掉 Mac iCloud 路径
- 验证：直接跑一次脚本，报错信息应只剩"数据源文件不存在"，而非路径逻辑错。

### 5. 验证隔离性
```bash
ls profiles/<name>/skills/      # 应为空
ls profiles/<name>/memories/    # 应为空（或仅模板）
cat profiles/<name>/config.yaml # 独立配置
hermes profile list             # 确认 default 未被切走
```

## 陷阱
- ❌ `hermes qiqiu setup` 直跑 → `invalid choice`。必须用 alias 包装或 `hermes -p qiqiu`。
- ❌ `setup` 在管道下不写盘（non-interactive）。改用 `config set`。
- ❌ 忘清 `.env` key 行尾注释 → 401 误判 key 失效。
- ⚠️ **微信通道是官方支持的**（`WEIXIN_*` iLinkAI 网关），不是 gewechat/wechaty 第三方桥接——别再对用户说"不支持微信"。
- ⚠️ **跨 profile cron 投递微信**：cron 跑在 default 上下文，必须先把目标 profile 的整套 `WEIXIN_*`（含 `WEIXIN_ACCOUNT_ID`）镜像进 default 的 `.env`，否则报 `platform 'weixin' not configured` 或 `Weixin account ID missing`。
- ⚠️ 从 Mac 迁来的 skill 含 `/Users/...` 或 `/Applications/...` 硬编码路径，在 Linux 必跑挂——先按 §4c 改 3 处路径（NODE_BIN / 数据源脚本 / 输出目录）再验证。

## 相关
- 实战产物：`qiqiu` profile（老婆/秋秋专属），SOUL.md 仍待按"秋秋"人格重写。
- 用户有 3 个品牌账号（秋秋/酒酒/新IP），可能复用此流程建更多 profile。
