# Twitter/X Ingest via xreach

## Tool

```bash
~/.npm-global/bin/xreach tweet "<tweet_id>"
```

Returns JSON with fields:
- `id`, `text`, `createdAt`
- `user.name`, `user.screenName`, `user.profileImageUrl`
- `viewCount`, `likeCount`, `retweetCount`, `replyCount`, `quoteCount`, `bookmarkCount`
- `media[].type`, `media[].url`, `media[].width`, `media[].height`
- `lang`, `isRetweet`, `isQuote`, `isReply`

## Tweet ID Extraction

From URL `https://x.com/<handle>/status/<tweet_id>` — the tweet ID is the last path segment.

From tweet JSON `id` field — this is the numeric tweet ID as a string.

## Filename Convention

```
raw/tweets/<screenName>-<tweetId>.md
```

Examples from this session:
- `raw/tweets/lidangzzz-2044673430901936512.md`
- `raw/tweets/pmbackttfuture-2050036759115833587.md`

## Raw Frontmatter Template for Tweets

```yaml
---
source_url: https://x.com/<handle>/status/<tweetId>
ingested: YYYY-MM-DD
author: <user.name>
username: <user.screenName>
platform: Twitter/X
content_status: direct | reconstructed
sha256: <hex>
---
```

- `content_status: direct` — full tweet text was fetched
- `content_status: reconstructed` — tweet was link-only, content reconstructed from public references
- `sha256`: compute over body only (everything after closing `---`)

## Content Notes

- Link-only tweets (`"https://t.co/..."` as text) mean the actual content is in the
  linked image/page or X Article. Follow the redirect with curl to find out:
  ```bash
  curl -sIL "https://t.co/..." | grep -i "^location:" | tail -1
  ```
- `lang: "zxx"` means language could not be detected — manual review may be needed.
- High `bookmarkCount` relative to `likeCount` suggests the content is especially
  worth filing (people bookmark for later reference more intentionally than they like).

## X Article Reconstruction Workflow

When a link-only tweet redirects to `x.com/i/article/<articleId>`:

1. **Get the article ID** from the redirect URL (the last path segment)

2. **Use the original tweet thread** to gather context — replies often discuss the article:
   ```bash
   xreach thread <original_tweet_id>
   ```

3. **Search for quote tweets** using the article topic or the author's summary post.
   Keywords: the author's own quote tweet + the article topic.
   ```bash
   xreach search "from:author_handle <topic keywords>"
   ```

4. **Search by article ID or URL** — other users may have quoted/paraphrased it:
   ```bash
   xreach search "<tweet_id>"
   xreach search "<article_topic>"
   ```

5. **Combine all fragments** into a cohesive summary. Common sources:
   - The author's own summary quote tweet
   - Reply threads discussing key points  
   - Other users' quote tweets that excerpt the article
   - Subsequent posts by the same author referencing the article

6. **Mark provenance**: Set `content_status: reconstructed` in raw file frontmatter.
   Set `confidence: medium` on derived concept/entity pages (not high — not the direct source).

7. **Save the raw file** with full reconstruction notes, not just the summary.
   Include the article ID so future attempts can try to fetch directly.

## Session Reconstruction Example

In a session (2026-05-19), a link-only tweet from @LufzzLiz (tweet 2042237123865297267)
redirected to article 2041878145427763204. Reconstruction used:
- Author's quote tweet (2042240298747834559) summarizing "10 things + 8 highlights"
- Reply thread engagement revealing article depth
- Quote tweet search finding detailed breakdowns
- Combined into `raw/tweets/LufzzLiz-2042237123865297267.md` + `concepts/Hermes Agent上手指南-岚叔.md`

Reconstruction quality was ~80-90% — enough for a concept summary with `confidence: medium`.

## Additional xreach Commands

```bash
# Get following list for a user
~/.npm-global/bin/xreach following <handle>

# Get user profile
~/.npm-global/bin/xreach user <handle>

# Get thread/conversation (includes replies)
~/.npm-global/bin/xreach thread <tweetId>

# Search tweets
~/.npm-global/bin/xreach search "<query>"
```

**`following` response structure:**
```json
{
  "items": [
    {
      "name": "User Name",
      "screenName": "handle",
      "description": "bio text",
      "followersCount": 12345,
      "followingCount": 99,
      "tweetCount": 999,
      "verified": false,
      "isBlueVerified": true,
      "protected": false,
      "location": "City",
      "url": "https://..."
    }
  ]
}
```

**Parsing pattern (Python):**
```python
import json
data = json.load(sys.stdin)
for u in data.get('items', []):
    print(f"@{u['screenName']} | {u['name']} | followers:{u['followersCount']} | {u.get('description','')[:80]}")
```

**Key fields:** `screenName` (handle), `followersCount`, `description`. Profile URL: `https://x.com/{screenName}`.

## Session Logged

- 2026-05-11: 5 tweets ingested (2 with full text, 2 link-only, 1 greenhandai with no content retrieved)
- Key finding: xreach returns metadata even for link-only tweets; content-not-retrieved tweets should still be filed with a note
- 2026-05-19: 1 X Article reconstructed from link-only tweet (LufzzLiz Hermes Agent guide) — added full reconstruction workflow and content_status frontmatter flag
