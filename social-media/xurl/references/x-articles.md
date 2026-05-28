# X Articles (Long-Form Posts) — Access Guide

X Articles are a content type distinct from regular tweets. They are rendered client-side and require authentication to view. A tweet linking to an X Article contains only a t.co URL in its text field.

## Identifying X Articles

- URL pattern: `https://x.com/i/article/{article_id}`
- The tweet's `text` field will be just `https://t.co/...` (the t.co redirect target)
- `xreach tweet {tweet_id}` returns the tweet metadata, but `text` is only the link
- The article_id is DIFFERENT from the tweet_id — do not use `xreach tweet {article_id}` (returns "Tweet not found")
- Resolve the t.co redirect: `curl -sIL "https://t.co/..." | grep -i "^location:" | tail -1` — extracts the real `x.com/i/article/{id}` URL

## Bypass Flow: Reconstruct Article Content

When direct access fails (login wall), reconstruct the article's key points from the social layer. This is a **three-pass approach**:

### Pass 1: Thread — Get Comment Context

```bash
xreach thread {tweet_id}
```

The author's replies to comments often reveal what the article covers. Look for:
- Author answering "what is this about" type questions
- Keywords mentioned in responses (SOUL.md, Skills, Auxiliary models, etc.)

### Pass 2: Search Topic — Find Quote Tweets with Full Content

```bash
# Search for the article's core topic
xreach search "核心关键词" -n 20

# Filter to quote tweets that paste bullet-point summaries
# Users often quote the article with "核心内容一览" or similar headers
```

**This is the most productive step.** Quote tweets that describe the article often paste the entire bullet-point structure into their text. The X API returns tweet text in full even if the original Article is behind a login wall.

### Pass 3: Author's Own Summary

```bash
# Search for the author's own quote tweets about the article
xreach search "from:{author_username} {article_id_or_keyword}"

# Or search for the author's quote tweet ID from Pass 1
xreach tweet {quote_tweet_id}
```

Authors often post a separate tweet summarizing their own article — this gives the most authoritative condensed version.

### Cross-Reference & Synthesize

- Compare content from multiple quote tweets — consistent patterns = likely accurate
- The replies section often has the author correcting misunderstandings, which reveals nuance
- Content search on X (not web search) since X Articles aren't indexed by Google

## Direct Access: Browser Cookie Injection (proven to work)

Two approaches — ephemeral (single session) and persistent (writes to Chrome profile disk).

### Approach A: Ephemeral — Browser Console Injection

Best for one-shot article reads using the built-in Hermes browser. Cookies last only for the current browser session — when the session ends, they're gone.

When xreach is already authenticated (confirmed via `xreach auth check`), inject its auth_token and ct0 into a browser session to view the full X Article content directly.

### Prerequisites

- **xreach already authenticated** (confirmed via `xreach auth check` returning "Authenticated")
- The auth tokens are stored at `~/.config/xfetch/session.json` — this is the file to read for actual auth_token and ct0 values
- If xreach auth check says "Not authenticated", the user needs to re-authenticate xreach first

### Cookie Source: Find Actual Token Values

`xreach auth check` masks token values (shows only first 10 chars). To get the full values:

1. **Read the session file** from where xreach stores auth tokens:
   ```
   ~/.config/xfetch/session.json
   ```
   Content format:
   ```json
   {
     "authToken": "71b021ca60...",
     "ct0": "442e332ffa..."
   }
   ```
   Read this file via `read_file` or `terminal` to get the full token strings.

2. **Only `auth_token` and `ct0` are required** — the `kdt` cookie is not needed for reading articles. Both `auth_token` and `ct0` from xfetch/session.json are sufficient.

### Steps

1. **Navigate to x.com** to establish a same-origin cookie context:
   ```
   browser_navigate('https://x.com')
   ```
   The page will show the login screen — this is expected. The important thing is setting the cookie domain to `.x.com` from this origin.

2. **Inject cookies via browser_console** (must be on x.com domain, not on a login redirect page):
   ```javascript
   document.cookie = "auth_token=VALUE; path=/; domain=.x.com; secure; samesite=lax;";
   document.cookie = "ct0=VALUE; path=/; domain=.x.com; secure; samesite=lax;";
   ```
   Verify with `document.cookie` — should return both cookies.

3. **Navigate to the article** (cookies persist within the same browser session):
   ```
   browser_navigate('https://x.com/i/article/{article_id}')
   ```
   The page renders the article content directly. The browser snapshot will show article text under `main` element.

4. **Extract full content** via browser_console — simplest approach uses `main.innerText`:
   ```javascript
   document.querySelector('main').innerText
   ```
   This returns the complete rendered article text, including headings, paragraphs, code blocks, and image alt text — all in a single string with proper line breaks. Much simpler than walking the DOM manually.

   If you need to filter or reformat, scroll the page first to ensure lazy-loaded content renders, then use the DOM query.

### Approach B: Persistent — Playwright Cookie Injection

When you need X login to persist across Chrome restarts (e.g. for VNC Chrome with Obsidian Web Clipper), use Playwright's `launch_persistent_context()` + `add_cookies()`. This writes cookies to disk in the Chrome profile's SQLite cookie store — they survive browser close and restart.

**Why this matters:** The `browser_console` approach (Approach A) only works within a single Hermes browser session. If you close that session and open a new one, X cookies are gone. Playwright's `add_cookies()` targets the persistent profile, so next time Chrome starts with the same `--user-data-dir`, X is still logged in.

**Prerequisites:**
- Playwright installed (`pip install playwright`)
- `xreach` already authenticated (tokens at `~/.config/xfetch/session.json`)
- A Chrome user data directory (either `~/.config/google-chrome` or a copy at `/tmp/`)

**Steps:**

1. **Read the auth tokens** from xreach's session file:
   ```
   ~/.config/xfetch/session.json  →  authToken and ct0
   ```

2. **Launch persistent context** with Playwright — this opens a headed Chrome on the VNC display:
   ```python
   from playwright.async_api import async_playwright
   
   browser = await p.chromium.launch_persistent_context(
       user_data_dir='/path/to/chrome-profile',
       headless=False,
       args=['--window-size=1280,900'],
   )
   ```

3. **Inject cookies** using Playwright's built-in API (bypasses Chrome's SQLite encryption):
   ```python
   await browser.add_cookies([
       {
           'name': 'auth_token',
           'value': '...',  # from ~/.config/xfetch/session.json
           'domain': '.x.com',
           'path': '/',
           'secure': True,
           'httpOnly': True,
           'sameSite': 'Lax',
       },
       {
           'name': 'ct0',
           'value': '...',  # from ~/.config/xfetch/session.json
           'domain': '.x.com',
           'path': '/',
           'secure': True,
           'httpOnly': False,
           'sameSite': 'Lax',
       },
   ])
   ```

4. **Navigate and verify** X is logged in:
   ```python
   page = await browser.new_page()
   await page.goto('https://x.com/', wait_until='networkidle')
   # Check for logged-in UI (profile name, navigation bar)
   title = await page.title()
   ```

5. **Keep the browser running** for VNC interaction:
   ```python
   while True:
       await asyncio.sleep(10)
   ```

**How cookie persistence works:** Playwright's `add_cookies()` calls CDP's `Storage.setCookies`, which writes to the profile's on-disk cookie store. Even after the Playwright script exits (and Chrome closes), the cookies remain in `/path/to/chrome-profile/Default/Cookies`. Next time you start Chrome with the same `--user-data-dir`, X is logged in automatically.

**Important:** The Playwright-launched browser has `--disable-extensions` by default. If you need extensions (e.g. Obsidian Web Clipper), you have two options:
- Use Playwright only for cookie injection, then kill it and start system Chrome with the same profile + `--load-extension`
- Or launch with system Chrome + `--remote-debugging-port` + `--remote-allow-origins=*` and connect Playwright to the running instance via `connect_over_cdp()`

**Verified working:** Session `20260526` — injected cookies persisted through Chrome restart, system Chrome started with `--user-data-dir=/tmp/cdp-chrome-profile` (copy of ~/.config/google-chrome) logged into X automatically.

### Save to Obsidian Vault

After extracting the article text, format it as a markdown file with frontmatter and save to the vault's `Clippings/` directory:

```
$VAULT/Clippings/{title-slug}.md
```

Frontmatter template:
```yaml
---
title: "Article Title"
source: "https://x.com/{author}/status/{tweet_id}"
domain: "x.com"
clipped: "{YYYY-MM-DD}"
author: "Author Name (@handle)"
---
```

Article body rendered as markdown with `##` for section headings. Code blocks preserved with triple backticks.

### Pitfalls

- Requires valid auth_token + ct0 cookies from a logged-in X session
- The cookie file is at `~/.config/xfetch/session.json`, not displayed in `xreach auth check` output
- Browser uses its own isolated cookie jar — injection must happen in the same session
- Setting cookies from a login redirect page fails (cross-origin security restriction); always navigate to x.com root first
- Cookies may expire — check `xreach auth check` first; if it says "Authenticated", cookies are still valid
- The browser may not render the article's cover image — that's fine, the text content still loads
- `browser_snapshot` truncates long articles; use `browser_console` with DOM queries to extract full text
- `main.innerText` captures everything including inline elements; be aware that very long articles may produce multi-KB output
- **auth_token is HttpOnly** — `document.cookie` will NOT show it after injection, but the browser still sends it automatically. Verify login by navigating to x.com and checking for logged-in UI (navigation shows "主页", "通知", "私信" etc.), not by inspecting document.cookie.

## Limitations

- No known API endpoint exposes raw X Article content without auth
- Browser automation (Browserbase/Camofox) with logged-in session might work but untested for X Articles specifically
- Article content is not indexed by Google/X search directly
- Archive.org likely won't have it (login wall blocks Wayback Machine saving)
- `xurl` CLI does NOT support X Articles — `xurl read {article_id}` returns "Tweet not found"
- `xreach` CLI cannot access Articles via `xreach tweet {article_id}` either (different endpoint from regular tweets)

## Real Example

See session `20260519_215003_e4ad3323` for a full walkthrough:
- Source tweet: `https://x.com/LufzzLiz/status/2042237123865297267`
- Article ID: `2041878145427763204`
- Method: xreach thread → xreach search for topic keywords → xreach search `from:LufzzLiz` for author's own quote tweet
- Result: Reconstructed all 10 configuration items + 8 highlights from the social layer alone

See session `20260522_104501` for a cookie injection walkthrough:\n- Article: `TTkitty_` Obsidian beginner tutorial\n- Method: browser cookie injection with auth_token + ct0 + kdt from xreach's authenticated session\n- Result: Full 12-section article text extracted via browser_console DOM queries\n\nSee session `20260527` for a cookie injection + Obsidian clipping walkthrough:
- Source tweet: `https://x.com/ai_xiaomu/status/2050007288560459820`
- Article ID: `2048775123893899264`
- Method: xreach auth check → read session.json → inject auth_token+ct0 (only two cookies, no kdt) → navigate to article → `document.querySelector('main').innerText` for extraction → formatted as Obsidian markdown with frontmatter → saved to `$VAULT/Clippings/`
- Result: Full 7.7KB article text saved. Confirmed auth_token is HttpOnly (not visible in document.cookie)\n- Source tweet: `https://x.com/ChrisWangwy/status/2058562162847592503`\n- Article ID: `2058526316862070784`\n- Method: read `~/.config/xfetch/session.json` for auth_token + ct0 → inject only these two cookies (no kdt needed) → navigate to article → `document.querySelector('main').innerText` for extraction\n- Result: Full 4.7KB article text saved to `$VAULT/Clippings/`
