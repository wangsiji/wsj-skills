# DeepSeek Provider Configuration

## DeepSeek V4 (deepseek-v4-pro) Setup

```bash
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-pro
hermes config set model.api_key sk-xxxxxxxxxxxxxxxxxxxxxxxx
hermes config set model.base_url https://api.deepseek.com
```

Key points:
- `provider` must be `deepseek` (not `deepseek-chat` or other string)
- `base_url` must be explicitly set to `https://api.deepseek.com` (defaults to MiniMax if not changed)
- Model name: `deepseek-v4-pro` or `deepseek-v4-flash`
- API key stored in memory as `sk-032f2c45088745c39e6f10e6a42bac36`

## Verify

```bash
grep -A5 "^model:" ~/.hermes/config.yaml
```

## DeepSeek Models Available

- `deepseek-v4-pro` — most capable
- `deepseek-v4-flash` — faster/cheaper
