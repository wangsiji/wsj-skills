# Cron → Telegram Delivery: `.env` Propagation Issue

## The Problem

When a cron job runs as a subprocess (via `cronjob` tool), it does NOT automatically inherit `.env` vars from `~/.hermes/.env`. Even though `load_gateway_config()` → `_apply_env_overrides()` is designed to read `TELEGRAM_BOT_TOKEN` from `os.getenv()`, the token is not in the subprocess environment.

**Symptom:**
```
{"error": "Platform 'telegram' is not configured. Set up credentials in ~/.hermes/config.yaml or environment variables."}
```

Yet `hermes cron list` shows `TELEGRAM_BOT_TOKEN` in `.env`, and the gateway (running as a long-lived daemon) works fine.

## Root Cause

`hermes cron` schedules jobs via `hermes_cli/cron.py` which passes env vars from the gateway session (`HERMES_CRON_AUTO_DELIVER_*`) to the subprocess, but does NOT read `~/.hermes/.env` and inject all its vars.

The `.env` file is loaded only by `hermes_cli/main.py` at CLI startup via `load_hermes_dotenv()`. Cron subprocesses are spawned via `agent.run_agent` or `scripts/run_hermes_cron.py` — they don't go through that startup path.

## Verified Fix: Direct Bot API (No Tool Layer)

For standalone Python scripts that need to send to Telegram without going through the hermes tool infrastructure:

```python
import os
import re
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

async def send_telegram(token, chat_id, message):
    bot = Bot(token=token)
    await bot.send_message(chat_id=int(chat_id), text=message, parse_mode=ParseMode.MARKDOWN_V2)

# Read token from .env manually
env_file = os.path.expanduser("~/.hermes/.env")
with open(env_file) as f:
    for line in f:
        k, _, v = line.strip().partition("=")
        if k == "TELEGRAM_BOT_TOKEN" and not os.getenv(k):
            os.environ[k] = v

token = os.environ["TELEGRAM_BOT_TOKEN"]
chat_id = os.environ.get("HERMES_CRON_AUTO_DELIVER_CHAT_ID", "7128007362")

asyncio.run(send_telegram(token, chat_id, "Your message"))
```

The markdown→MarkdownV2 formatting is handled by `gateway/platforms/telegram.py`'s `format_message()` if available; fallback is plain text.

## Alternative: hermes cron job with `deliver=telegram:CHAT_ID`

If the job's `deliver` is set to a specific Telegram target (e.g. `telegram:7128007362`) instead of `origin`, the cron scheduler resolves the platform from `HERMES_CRON_AUTO_DELIVER_*` env vars that ARE passed to the subprocess. The `_apply_env_overrides()` reads `os.getenv("TELEGRAM_BOT_TOKEN")` which would be set if the token was loaded — but it isn't because the subprocess doesn't have the full `.env`.

**Fix:** Ensure `TELEGRAM_BOT_TOKEN` is available in the subprocess by having the cron job's shell wrapper source it, OR use the direct Bot API approach above.

## Env Vars That ARE Passed to Cron Subprocesses

These are explicitly set by the cron scheduler:
- `HERMES_CRON_AUTO_DELIVER_PLATFORM`
- `HERMES_CRON_AUTO_DELIVER_CHAT_ID`
- `HERMES_CRON_AUTO_DELIVER_THREAD_ID`
- `HERMES_SESSION_PLATFORM=telegram`
- `HERMES_SESSION_KEY`

The token (`TELEGRAM_BOT_TOKEN`) is NOT automatically passed — it's only in the gateway daemon's environment.

## Relevant Code

- `_apply_env_overrides()` in `gateway/config.py:1239` — reads `os.getenv("TELEGRAM_BOT_TOKEN")` and enables Telegram
- `cron/scheduler.py` — `_resolve_single_delivery_target()` resolves `origin` delivery using `HERMES_CRON_AUTO_DELIVER_*`
- `tools/send_message_tool.py:757` — `_send_telegram()` is the one-shot Bot API sender used by the scheduler's standalone path
