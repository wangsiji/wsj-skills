# X/Twitter Article URL — `/i/article/` Pages Cannot Be Read Without Login

## Problem

X's article pages (`https://x.com/i/article/<id>`) render content via JavaScript and are gated behind login authentication. Every bypass method tested has failed.

## Methods That Do NOT Work

| Method | Result |
|--------|--------|
| `curl` / Jina Reader / any HTTP fetch | Returns X login wall |
| Nitter instances (privacydev.net, poast.org, nitter.net) | CF verification or 403 |
| syndication.twitter.com | Rate limited |
| `t.co` short link resolution | Redirects to login-gated article page |

## What DOES Work

1. **User provides article text directly** — fastest, most reliable
2. **User provides article title** → search elsewhere for full text
3. **`xreach thread <id>`** — the thread's replies and quote tweets often contain excerpts, the author's own replies, or reactions that reveal the article's content. Check this first before telling the user you can't read it.

## Practical Workflow for an X Article URL

```
1. xreach tweet <id or URL>           # get the tweet itself
2. xreach thread <id>                 # get replies/quote tweets for context
3. If tweet text has a summary/paste of article content → use that
4. If only a bare link → check replies → still empty → ask user to paste text
```

## Example from Session (2026-05-19)

Tweet `2042237123865297267` from @LufzzLiz: bare `t.co` link in tweet text, zero content via all bypass attempts. Thread replies revealed:
- Someone asked author for "soul.md" → author said "article里有"
- Comment: "这个源代码比OpenClaw少，是用Python写的"
- Author recommended a skill for safe X reading

→ Thread context alone gave a rough topic (Python AI agent tool, compared to OpenClaw), even without the full article.
