# 精简 config.yaml 模板

Hermes Agent 默认 config.yaml 约 500 行。只需保留以下核心部分即可正常运行，其他未设置的项自动使用内置默认值。

## 最小配置

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com

providers:
  deepseek:
    name: deepseek
    base_url: https://api.deepseek.com
    models:
    - deepseek-v4-flash
    - deepseek-v4-pro

toolsets:
- hermes-cli

agent:
  max_turns: 90

terminal:
  backend: local

compression:
  enabled: true

auxiliary:
  vision:
    provider: qwen-portal
    model: vision-model

memory:
  memory_enabled: true
  user_profile_enabled: true

cron:
  cron_mode: approve
```

## 清理原则

1. API key 放 `.env`，不放 `config.yaml`
2. 未设置的值使用内置默认值，不需要显式写出来
3. 只保留实际修改过的配置项
4. `command_allowlist` 保留 `.*` 通配即可
