# Alternative Image Generation Backends

When `image_generate` tool is unavailable, use these fallbacks in order.

## 1. infsh CLI (inference.sh)

Requires API key with credits. Install: `curl -fsSL https://cli.inference.sh | sh`

```bash
infsh login --key <your-key>

# Seedream 4.5 (best quality, cinematic)
infsh app run bytedance/seedream-4-5 --input '{
  "prompt": "...",
  "aspect_ratio": "16:9"
}'

# FLUX Klein (fast)
infsh app run falai/flux-2-klein-lora --input '{"prompt": "..."}'
```

**Pitfalls:** Insufficient balance returns `"Failed to submit task: insufficient balance"`. Check at https://app.inference.sh/settings/billing.

## 2. Pollinations.ai (Free, No Auth)

URL format: `https://image.pollinations.ai/prompt/{prompt}?width=W&height=H&nologo=true&seed=N`

```bash
curl -sL "https://image.pollinations.ai/prompt/Your%20prompt%20here?width=768&height=768&nologo=true&seed=42" \
  -o output.png
```

**Parameters:**
- `width`, `height` — in pixels (max ~1024)
- `nologo=true` — removes watermark
- `seed=N` — reproducibility

**Limits:**
- ~1 concurrent request per IP (returns JSON error `"Queue full for IP: X"` when exceeded)
- 768×768 max reliable resolution; higher may timeout
- Model is loose/creative, not photorealistic

**Status codes on error:** The returned file will be JSON, not an image. Check with `file output.png` — if it says "JSON text data", the request was rejected.

## 3. ComfyUI

Requires local GPU or Comfy Cloud API key. See the [comfyui skill](../comfyui/SKILL.md) for full setup instructions.

## Aspect Ratio Mapping

| Requested | `image_generate` enum | Pollinations URL params |
|-----------|----------------------|------------------------|
| 16:9      | `landscape`          | `width=1280&height=720` |
| 1:1       | `square`             | `width=768&height=768` |
| 9:16      | `portrait`           | `width=720&height=1280` |
