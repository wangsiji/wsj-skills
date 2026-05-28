# RSSHub Setup & Troubleshooting

## Docker Setup

```bash
docker run -d \
  --name rsshub \
  -p 8280:1200 \
  --restart unless-stopped \
  diygod/rsshub
```

## Platform Routes

| Platform | RSSHub Route | Notes |
|----------|-------------|-------|
| B站 | `/bilibili/user/video/:mid` | ⚠️ Fallback only. Prefer `bilibili-api-python` directly (see `references/bilibili-api-notes.md`). Cloudflare blocks most datacenter IPs. |
| 即刻 | `/jike/user/:uid` | UID from web.okjike.com/u/{uid} |
| 小宇宙 | `/xiaoyuzhou/podcast/:pid` | PID from xiaoyuzhoufm.com/podcast/{pid} |

## Playwright in Docker (for RSSHub routes that need it)

Some RSSHub routes (e.g. Twitter, Instagram) fall back to headless browser when API is blocked. Install Playwright:

```bash
# Inside container
docker exec rsshub npx playwright install chromium

# Install system deps first if needed
docker exec rsshub sh -c "apt-get update && apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2"

# Restart after installation
docker restart rsshub
```

> **Note**: For B站 specifically, Playwright inside RSSHub won't help — Cloudflare blocks from datacenter IPs regardless. Use `bilibili-api-python` directly instead.

## Version Mismatch Issue

If RSSHub Docker image was built with Playwright v1.52 (browser-1217) but npm installed v1.60 (browser-1223), the old version path persists in the container. The error shows:

```
Executable doesn't exist at .../chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell
```

Solution: run `npx playwright install --with-deps chromium` inside the container to get the version matching the installed Playwright library.

## Cloudflare Block

B站 API is heavily protected by Cloudflare. Even RSSHub + Playwright may fail from datacenter IPs because:
- B站 blocks known datacenter IP ranges
- Cloudflare challenge pages require JavaScript rendering
- headless Chromium may still trigger detection

**Preferred solution**: Use `bilibili-api-python` + `curl_cffi` directly instead of RSSHub for B站.
See `references/bilibili-api-notes.md` for the working approach.

**Legacy workaround**: Use a residential proxy or skip B站 source entirely.
