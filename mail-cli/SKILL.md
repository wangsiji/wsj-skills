---
name: mail-cli
description: ClawEmail (claw.163.com) 命令行工具，操作 Agent 邮箱 — 读邮件、搜索、发送、管理邮箱账号。支持多 profile、多邮箱切换，--json 输出适合脚本调用。
category: productivity
---

# mail-cli — ClawEmail 命令行工具

## 安装与路径

```bash
# 已在服务器安装（npm global）
~/.npm-global/bin/mail-cli

# 建议加 alias 或 link 到 PATH
ln -sf ~/.npm-global/bin/mail-cli /usr/local/bin/mail-cli
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--profile <name>` | 使用命名配置（多账号） |
| `--json` | JSON 格式输出（脚本用） |
| `--verbose` | 显示详细协议交互 |
| `--config <path>` | 自定义配置文件路径 |

## 认证流程（首次使用）

```bash
# 1. 设置 API Key（用于 clawemail 管理命令）
mail-cli auth apikey set <your_api_key>

# 2. 登录 Claw 主账户（配置 IMAP/SMTP）
mail-cli auth login --user youragent@claw.163.com

# 3. 验证认证状态
mail-cli auth test

# 4. 列出所有 profile
mail-cli auth list
```

## clawemail — Agent 邮箱管理

**需要先 `auth apikey set`**

```bash
# 列出工作区所有邮箱
mail-cli clawemail list
mail-cli clawemail list --json

# 创建子邮箱
mail-cli clawemail create --prefix bot1 --type sub --display-name "My Bot"

# 查看邮箱详情
mail-cli clawemail info
mail-cli clawemail info --uid bot1@claw.163.com

# 更新显示名
mail-cli clawemail profile --uid bot1@claw.163.com --display-name "New Name"

# 启用 / 禁用 / 删除
mail-cli clawemail enable --uid bot1@claw.163.com
mail-cli clawemail disable --uid bot1@claw.163.com
mail-cli clawemail delete --uid bot1@claw.163.com
```

## folder — 文件夹操作

```bash
# 列出所有文件夹
mail-cli folder list
mail-cli folder list --json
```

## mail — 邮件操作

```bash
# 列出邮件（--fid 可用数字 ID 或 INBOX/Sent/Draft/Trash 等名称）
mail-cli mail list --fid INBOX --limit 20 --desc
mail-cli mail list --fid 1 --unread --order date

# 获取指定邮件（多 ID 用逗号分隔）
mail-cli mail get --ids "msg1,msg2"
mail-cli mail get --ids "msg1" --fid INBOX

# 搜索邮件
mail-cli mail search --fid INBOX --keyword "report" --limit 10
mail-cli mail search --fid INBOX --from "boss@example.com" --unread
mail-cli mail search --fid INBOX --keyword "invoice" --fts  # 全文搜索
mail-cli mail search --fid INBOX --since 2026-01-01 --before 2026-01-31

# 移动邮件
mail-cli mail move --ids "msg1,msg2" --to-fid Trash --fid INBOX

# 标记已读/未读
mail-cli mail mark --ids "msg1,msg2" --fid INBOX --read
mail-cli mail mark --ids "msg1" --fid INBOX --unread

# 实时监听新邮件（NDJSON 流）
mail-cli mail watch
mail-cli mail watch --quiet  # 静默模式
```

## read — 读取邮件内容

```bash
# 读取正文（--fid 对 IMAP 账户必填）
mail-cli read body --id <msg_id> --fid INBOX
mail-cli read body --id <msg_id> --fid INBOX --raw  # 输出原始 HTML

# 读取邮件头
mail-cli read header --id <msg_id> --fid INBOX

# 查看 MIME 结构（含附件列表）
mail-cli read structure --id <msg_id> --fid INBOX

# 下载附件
mail-cli read attachment --id <msg_id> --part-id <partId> --out-file ./downloaded.zip
```

## compose — 发送邮件

```bash
# 发送邮件
mail-cli compose send \
  --to user@example.com \
  --subject "主题" \
  --body "正文"

# 带附件、抄送、密送
mail-cli compose send \
  --to user@example.com \
  --cc cc@example.com \
  --bcc bcc@example.com \
  --subject "主题" \
  --body "正文" \
  --attachment ./file.pdf \
  --attachment ./image.png

# 回复邮件
mail-cli compose reply --id <msg_id> --fid INBOX --body "回复内容"

# 转发邮件
mail-cli compose forward --id <msg_id> --fid INBOX --to someone@example.com
```

## 典型工作流

### 查邮件
```bash
# 1. 先看文件夹
mail-cli folder list --json

# 2. 列出 INBOX 最近 10 封
mail-cli mail list --fid INBOX --limit 10 --desc --json

# 3. 读某封
mail-cli read body --id <msg_id> --fid INBOX
```

### 搜索 + 读 + 回调
```bash
# 搜索
mail-cli mail search --fid INBOX --keyword "发票" --limit 5 --json

# 下载附件
mail-cli read structure --id <msg_id> --fid INBOX
# 找到 partId 后
mail-cli read attachment --id <msg_id> --part-id "2" --out-file ./invoice.pdf
```

### 多账号切换
```bash
# 创建时自动生成 profile
mail-cli clawemail create --prefix newbot --type sub --display-name "NewBot"

# 用指定 profile 操作（无需每次 login）
mail-cli --profile newbot mail list --fid INBOX
mail-cli --profile newbot compose send --to xxx --subject "Hi" --body "Hello"
```

### AI 实时处理（mail watch）
```bash
# 监听新邮件，流式处理（适合接 AI）
mail-cli mail watch --quiet --json | while read line; do
  echo "$line" | jq -r '.subject'
  # 在此调用 AI 处理
done
```

## 注意事项

- API Key (`auth apikey set`) 仅用于 `clawemail` 管理命令（创建/删除邮箱等）
- 日常邮件读写只需 `auth login` 后的 IMAP 认证，不需要 API Key
- `--json` 输出适合脚本解析，省去文本解析麻烦
- `--verbose` 用于调试协议交互问题
- 邮件 ID 是字符串（带引号），不是数字索引
- Linux 服务器无钥匙串，API Key 存放在 `~/.config/mail-cli/config.json` 的 `apikeyRef` 字段引用系统 keyring（如果 keyring 不可用，可能需要直接配置 key）
