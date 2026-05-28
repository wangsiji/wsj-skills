# 秋秋 Content Ecosystem — 双账号内容策略

## Data Sources (Scraper Structure)

Scraped data at `/home/wangsiji/projects/wsj-scrapy-gzh/` covers **4 accounts**:

| Directory | Account | Articles |
|-----------|---------|----------|
| 秋秋很开心 | **秋秋很开心** — your account | 255 |
| 秋秋在分享 | **秋秋在分享** — your account | 227 |
| 数字生命卡兹克 | 数字生命卡兹克 — third-party (AI tech) | 673 |
| 六镇 | 六镇 — third-party (social commentary) | 55 |

## Dual-Account Positioning

| Dimension | 秋秋很开心 | 秋秋在分享 |
|-----------|-----------|-----------|
| Positioning | Tools + Growth, personal practice | FIRE (Financial Independence, Retire Early) |
| Style | Personal "look what I did" | FIRE how-to "how to be FI" |
| Content | Study, journaling, efficiency, app reviews, finds | FIRE methodology, saving, investing, real estate |
| Audience | People learning to improve their life | People learning to achieve FI |

**Never confuse:**
- 秋秋在分享 is **not** an AI/tech account. AI content belongs to 数字生命卡兹克.
- 秋秋在分享 is **not** a social commentary account. That's 六镇.
- 秋秋在分享 is a pure FIRE brand.

## Content Attribution Rules

### 秋秋在分享 (FIRE)
- FIRE financial how-to, saving methods, portfolio allocation
- Early retirement diaries: living on interest, geo-arbitrage, real estate
- 4% Rule, passive income, location independence
- **Readers come to learn financial freedom**

### 秋秋很开心 (Tools + Growth)
- Study methods, time management, journaling techniques
- App/tool recommendations, lifestyle finds
- Self-discipline habits, personal growth reflections
- **Readers come to learn how to live better**

### AI Content Filter Frame (for 秋秋很开心)

If you want to introduce AI content into 秋秋很开心, it MUST follow:

**秋秋开心的 AI angle:** Personal practice by 秋秋, with 秋秋 as the protagonist
- ✗ "this AI tool is powerful" (technical review)
- ✅ "I used AI to do X, saved 2 hours" (personal story)
- ✗ Prompt tips, model comparisons
- ✅ AI helped write reading notes, AI helped make weekly plans
- ✗ Technical benchmarks
- ✅ Lifestyle method

**One-sentence filter:** "If you replaced AI with any other tool, would this article still stand?"
- Yes → 秋秋很开心 (focus on practice)
- No → Not even 秋秋在分享 can save it (this topic isn't right for 秋秋)

## Vector DB Historical Bug (2026-05-21 Fixed)

Previously `build_index.py` had a binary label (秋秋很开心 vs everything-as-秋秋在分享), causing 数字生命卡兹克 and 六镇 articles to be mislabeled as 秋秋在分享. Fixed to independent labeling per account.

**Rebuild command:**
```bash
cd /home/wangsiji/projects/info-feed
source .venv/bin/activate
python3 -c "
import os; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from build_index import load_all_articles, build_index
chunks = load_all_articles()
build_index(chunks)
"
```

Takes ~5-10 min (6299 chunks). Compare account distribution before/after to confirm.

## Semantic Search Integration

When the user asks "秋秋之前写过XX吗" or "秋秋有没有写过XX", use the agent-integrated search:

```bash
cd /home/wangsiji/projects/info-feed
source .venv/bin/activate
python3 qiuyu_search.py "search query"
```

Returns structured JSON with title, account name, URL, pub_date, score, and preview. Parse results and present top matches with source attribution.
