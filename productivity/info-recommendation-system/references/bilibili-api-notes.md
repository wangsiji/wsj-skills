# B站 API Access Notes

## The Problem

B站 uses multiple layers of anti-bot protection:
1. **Cloudflare WAF** — blocks datacenter IP ranges at the HTTP layer
2. **WBI Signature** — API requests need a dynamically-generated sign parameter (rotates ~daily)
3. **buvid3/buvid4 device fingerprint** — tracks unique devices; requests without valid buvid get -352 风控校验失败
4. **Rate limiting** — after 1-3 requests from the same IP, returns HTTP 412 with Cloudflare challenge page

## The Solution: bilibili-api-python + curl_cffi

```bash
pip install bilibili-api-python curl_cffi
```

`bilibili-api-python` handles WBI signing internally. `curl_cffi` impersonates Chrome 131+ TLS fingerprint, bypassing Cloudflare's TLS-level detection.

## Working Code (Basic)

```python
import asyncio
from bilibili_api import user

async def get_latest_videos(uid: int, count: int = 5):
    u = user.User(uid)
    data = await u.get_videos(ps=count, pn=1)
    return data.get("list", {}).get("vlist", [])

# Each vlist item fields:
#   title, bvid, created (unix ts), play, comment, video_review (danmaku)
#   length (e.g. "08:50"), description, pic (thumbnail URL), author, mid
```

## Working Code (with Cookie Auth — 100% Success Rate)

### 1. Export cookies from browser

Use an extension like **Cookie-Editor** or **EditThisCookie** to export `.bilibili.com` cookies as JSON. The essential fields:

| Cookie Name | Value Example | Purpose | Required |
|-------------|--------------|---------|----------|
| `SESSDATA` | `a7857d51%2C1794796864%2C...` | Login session token | ✅ Critical |
| `bili_jct` | `fe51790a79e0f4bb0168ce642d150d81` | CSRF token (write ops) | ✅ Strongly recommended |
| `DedeUserID` | `214464850` | Your B站 user ID | ✅ |
| `buvid3` | `9E7B1FDB-4068-3306-0454-0287E7F3FD1F31933infoc` | Device fingerprint | ✅ |
| `buvid4` | `75D2A645-DF62-876E-601C-9A99DBE7201234186-...` | Device fingerprint v2 | ✅ |
| `_uuid` | `E94E9FBD-FCB1-E6F0-38CC-97B72F4804B469137infoc` | Additional device ID | 👍 Nice to have |
| `buvid_fp` | `23c37fa894f9c17466893f0ed82d899b` | Fingerprint hash | 👍 Nice to have |

### 2. Store credentials in `.env.bilibili`

```
# ~/projects/info-feed/.env.bilibili
BILIBILI_SESSDATA=a7857d51%2C1794796864%2C...
BILIBILI_BILI_JCT=fe51790a79e0f4bb0168ce642d150d81
BILIBILI_DEDE_USER_ID=214464850
BILIBILI_BUVID3=9E7B1FDB-4068-3306-0454-0287E7F3FD1F31933infoc
BILIBILI_BUVID4=75D2A645-DF62-876E-601C-9A99DBE7201234186-026021214-PDjWCsX5QZWqTvlAezM+tA%3D%3D
```

**Security**: add this file to `.gitignore`. The recaller reads it at module load time.

### 3. Use with Credential

```python
from bilibili_api import Credential, user

cred = Credential(
    sessdata="a7857d51%2C1794796864%2C...",
    bili_jct="fe51790a79e0f4bb0168ce642d150d81",
    dedeuserid="214464850",
    buvid3="9E7B1FDB-4068-3306-0454-0287E7F3FD1F31933infoc",
    buvid4="75D2A645-DF62-876E-601C-9A99DBE7201234186-...",
)
u = user.User(uid, credential=cred)
data = await u.get_videos(ps=10, pn=1)
```

### 4. Verify credential is loaded

```python
cred = _load_credential()
print(f"has_sessdata: {cred.has_sessdata()}")
```

## Success Rates

| Configuration | Success Rate | Notes |
|--------------|-------------|-------|
| No credential (anonymous) | ~50-75% | Gets 412 after 1-3 requests |
| With buvid3 only | ~60-80% | Modest improvement |
| With SESSDATA + buvid3 + buvid4 | **~100%** | No 412 errors even with 5s delays |

## Rate Limiting Strategy

Even with full credentials, maintain discipline:

```python
for each UP主:
    try:
        videos = await fetch(uid)
        process items
    except NetworkException (412):
        await asyncio.sleep(15)
        try again once
    finally:
        await asyncio.sleep(5 + random.uniform(0, 2))
```

With credentials, 412 is rare but still possible. Always add retry logic.

## Getting Correct UIDs

Use bilibili_api.search to find UP主 by name:

```python
from bilibili_api import search, sync

result = sync(search.search_by_type("影视飓风", search.SearchObjectType.USER, page=1))
for r in result.get("result", []):
    print(f"UID={r['mid']}: {r['uname']}")
```

Common tech UP主 UIDs:

| Name | UID |
|------|-----|
| 老师好我叫何同学 | 163637592 |
| 影视飓风 (MediaStorm) | 946974 |
| 极客湾Geekerwan | 25876945 |
| 小宁子 | 419738 |
| TESTV | 927487 |
| 李大锤同学 | 35248841 |
| 门冬冬 | 14097567 |

## Cookie Expiry

- SESSDATA typically expires in ~30 days (check `expirationDate` in cookie export)
- Refresh by re-exporting from browser when recall starts failing
- bili_jct may expire independently — export all cookies together

## Alternative: Get笔记 API (One-off Transcription)

`qiaomu-anything-to-notebooklm` uses Get笔记 API for individual video transcription:
- POST B站 URL to `https://openapi.biji.com/open/api/v1/resource/note/save`
- Wait 2-20 min for transcription
- Fetch full transcript text with timestamps

Not suitable for continuous monitoring — designed for single-video use.

## What Doesn't Work

- **Direct curl to api.bilibili.com** → -352 风控校验失败 (no WBI sign)
- **RSSHub B站 route** → Cloudflare blocks from datacenter IPs
- **Playwright/headless browser** → B站 detects headless Chrome via JS checks
- **Requests/httpx** → missing Chrome TLS fingerprint → blocked by Cloudflare
- **Fake buvid3** (random UUID) → instantly blocked. Must use a real browser-generated one.
