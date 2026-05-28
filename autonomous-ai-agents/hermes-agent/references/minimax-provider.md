# MiniMax Provider Configuration

## Two Built-in Providers

Hermes has **two** built-in MiniMax providers. Using the wrong one causes 401 errors.

| Provider | Endpoint | Region | Auth Header |
|----------|----------|--------|-------------|
| `minimax` | `https://api.minimax.io` | International | MiniMax native |
| `minimax-cn` | `https://api.minimaxi.com/anthropic` | China (Anthropic API compatible) | X-Api-Key |

## For MiniMax Anthropic-Compatible API (Chinese mainland)

The `minimax-cn` provider uses `https://api.minimaxi.com/anthropic` with Anthropic-format headers.

### Setup

```bash
# 1. Set env var (NOT in config.yaml — built-in provider reads from env)
echo 'MINIMAX_CN_API_KEY=sk-cp-xxxxxxxxxxxxxxxxxxxxxxxx' >> ~/.hermes/.env

# 2. Switch to the provider
hermes config set model.provider minimax-cn
```

### DO NOT create a custom provider named `minimax` or `minimax-cn`

If you define a provider block with the same name in `providers:` in config.yaml, it conflicts with the built-in one. The built-in provider silently wins for base URL and auth format, but your config's api_key may not be read correctly.

**Wrong** (causes 401 — built-in dodges your custom definition):
```yaml
providers:
  minimax-cn:
    name: minimax-cn
    api_key: sk-cp-xxx   # ignored; built-in overrides
```

**Correct** (use env var instead):
```bash
echo 'MINIMAX_CN_API_KEY=sk-cp-xxx' >> ~/.hermes/.env
```

### Common Pitfall: `provider: minimax` vs `minimax-cn`

The built-in `minimax` provider targets the International endpoint (`api.minimax.io`). If your key was issued for the China endpoint (`api.minimaxi.com/anthropic`), setting `model.provider: minimax` in config.yaml will fail.

**Symptom**: Model loading hangs/times out, `hermes doctor` passes but chat fails.
**Fix**: Change to `provider: minimax-cn`.

---

## Available Models (verified 2026-05-16)

Text models only — **MiniMax has NO vision/VLM model**:

| Model | Type | Vision? |
|-------|------|---------|
| MiniMax-M2.7 | text | no |
| MiniMax-M2.7-highspeed | text | no |
| MiniMax-M2.5 | text | no |
| MiniMax-M2.1 | text | no |
| MiniMax-M2 | text | no |
| image-01 | image generation | **no** (generation only) |
| speech-2.8-hd/turbo | speech | no |
| MiniMax-Hailuo-* | video | no |
| music-2.6 | music | no |

**`MiniMax-VL-01` does not exist.** `image-01` is image generation (text-to-image), NOT image understanding. Any config trying to use MiniMax for vision will fail with `unknown model (2013)`.

---

## Vision / Image Understanding — Working Config

Use MiniMax for text + DeepSeek for vision:

```yaml
provider: minimax-cn
model: minimax-portal/MiniMax-M2.7

auxiliary:
  vision:
    provider: deepseek
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com
    api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
    timeout: 120
    extra_body: {}
    download_timeout: 30
```

**Restart gateway after config change:**
```bash
pkill -f hermes-gateway; hermes gateway start &
```

### Image URL requirements for `vision_analyze`

**Does NOT accept:**
- `file://` local paths
- `http://localhost:*` or `http://127.0.0.1:*` URLs
- Twitter/X `https://pbs.twimg.com/media/...` URLs (often 404 or blocked)

**Accepts:**
- Public HTTPS URLs returning direct image data
- Images through browser tool (navigate → browser_vision)

**For local images**: Upload directly to the chat as a file attachment — the model receives it natively without `vision_analyze`.