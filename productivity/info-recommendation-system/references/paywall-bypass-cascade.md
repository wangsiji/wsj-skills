# Paywall Bypass Cascade

Reference: [qiaomu-anything-to-notebooklm](https://github.com/joeseesun/qiaomu-anything-to-notebooklm) — 6-level cascading paywall bypass learned from Bypass Paywalls Clean.

## Bypass Strategy (6-Level Cascade)

```
Level 1: Proxy services (r.jina.ai / defuddle.md)
    ↓ fail
Level 2: Site-specific bot UA (Googlebot ~50 sites / Bingbot ~4 sites)
    ↓ fail
Level 3: Generic bypass (UA spoof + X-Forwarded-For + Referer spoof + AMP + EU IP)
    ↓ fail
Level 4: archive.today cache (with CAPTCHA detection)
    ↓ fail
Level 5: Google Cache
    ↓ fail
Level 6: agent-fetch local tool
```

## Implementation Pattern

```bash
# Core loop in fetch_url.sh:

OUT=$(_curl --max-time 20 "https://r.jina.ai/$URL")
_try_output "$OUT"

OUT=$(_curl --max-time 20 "https://defuddle.md/$URL")
_try_output "$OUT"

# If domain matches GOOGLEBOT_DOMAINS:
OUT=$(_curl -H "User-Agent: Googlebot/2.1" -H "X-Forwarded-For: 66.249.66.1" -H "Referer: https://www.google.com/" -b "" "$URL")

# JSON-LD extraction fallback:
ARTICLE=$(_extract_jsonld_article "$OUT")  # grep 'articleBody' from <script type="application/ld+json">

# AMP page redirects:
AMP_URL="${URL}/amp" || "${URL}?outputType=amp" || "${URL}.amp.html"
OUT=$(_curl "$AMP_URL")

# archive.today as last resort:
ARCHIVE_URL="https://archive.today/newest/$URL"
OUT=$(_curl "$ARCHIVE_URL")
```

## Key Techniques

### Site-specific Googlebot domains (~50 sites)
```
wsj.com|barrons.com|ft.com|economist.com|theaustralian.com.au
thetimes.co.uk|telegraph.co.uk|zeit.de|handelsblatt.com
leparisien.fr|nzz.ch|usatoday.com|quora.com
lefigaro.fr|lemonde.fr|spiegel.de|sueddeutsche.de
smh.com.au|theage.com.au|brisbanetimes.com.au
```

### Bingbot domains (4 sites)
```
haaretz.com|nzherald.co.nz|stratfor.com|themarker.com
```

### Googlebot Bypass Command
```bash
curl -sL --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  -H "X-Forwarded-For: 66.249.66.1" \
  -H "Referer: https://www.google.com/" \
  -H "Accept: text/html,application/xhtml+xml" \
  -b "" \
  "$URL"
```

### JSON-LD Article Extraction
```bash
_extract_jsonld_article() {
  local html="$1"
  echo "$html" | grep -o '"articleBody":"[^"]*"' | head -1 | \
    sed 's/^"articleBody":"//;s/"$//' | sed 's/\\n/\n/g; s/\\"/"/g; s/\\\\/\\/g'
}
```

## Content Validation (`_has_content`)

```bash
_has_content() {
  local content="$1"
  # More than 8 lines
  [ "$(echo "$content" | wc -l)" -gt 8 ] || return 1
  # More than 500 chars
  [ "$(echo "$content" | wc -c)" -gt 500 ] || return 1
  # No paywall/login indicators
  echo "$content" | grep -q "Don't miss what's happening" && return 1
  echo "$content" | grep -qE '(Access Denied|404 Not Found|403 Forbidden)' && return 1
  return 0
}
```

## Paywall Detection

```bash
_is_paywall_content() {
  echo "$content" | grep -qiE \
    '(subscribe to (continue|read|access|unlock)|paywall|premium[._]content|'\
'metered[._]paywall|article[._]limit|sign[._]in[._]to[._](continue|read)|'\
'create[._]a[._]free[._]account[._]to[._]unlock|'\
'membership[._]to[._]continue|subscribe now for full access|'\
'to continue reading|remaining free articles|has been removed|'\
'subscribe or|already a subscriber)'
}
```

## Usage in info-recommendation-system

This cascade is useful when:
1. A Twitter/X post links to a paywalled article (NYT/WSJ/FT/Economist etc.)
2. The link should be included in the daily digest with full content summary
3. The article is behind a metered/soft paywall that the cascade can bypass

The cascade script is standalone (no external dependencies beyond curl and standard Unix tools). Copy `fetch_url.sh` pattern as-is for URL content extraction.

## What It Doesn't Bypass

- **Hard paywalls**: Some sites (The Information) never send the article body server-side, even to Googlebot. Only archive.today works, and it may require human CAPTCHA.
- **JavaScript-rendered content**: The cascade only fetches server-rendered HTML. Single-page apps need a headless browser.
- **Login-gated content**: Sites requiring account creation (not just subscription) won't work.
