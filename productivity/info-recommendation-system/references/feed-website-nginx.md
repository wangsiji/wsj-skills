# Feed Website: nginx + Generation Details

## nginx Location Block

Place inside the main server block (`server_name wangsiji.site dashboard.wangsiji.site`):

```nginx
# INFO FEED — 公开访问, 无认证
location /feed {
    auth_basic off;
    alias /var/www/info-feed/;
    try_files $uri $uri/ /feed/index.html =404;
}
```

Key points:
- `alias` not `root`: `/feed/` prefix stripped before mapping to filesystem
- `auth_basic off`: overrides root-level basic auth
- `try_files ... /feed/index.html.html =404`: SPA-friendly fallback

## Generator Script Structure (`~/projects/aihot-local/generate.py`)

```python
# 1. Import and call info-feed recallers (same as feed.py)
# 2. Collect all items, sorted by created_at desc
# 3. Format each item into HTML card string
# 4. Read template, replace ITEMS_PLACEHOLDER with cards
# 5. Write to output/index.html
# 6. Rsync to nginx serve dir
```

### Rsync deployment

```bash
rsync -a ~/projects/aihot-local/output/ /var/www/info-feed/
```

Runs as the `wangsiji` user. Needs `sudo` for `/var/www/info-feed/` write unless permissions adjusted:
```bash
sudo chown -R wangsiji:wangsiji /var/www/info-feed/
```

### Item HTML Card Format

```
<div class="item" data-type="{{ type }}">
  <div class="item-meta">
    <span class="tag tag-{{ type }}">{{ type_label }}</span>
    <span>{{ author }}</span>
  </div>
  <div class="item-title"><a href="{{ url }}" target="_blank">{{ title }}</a></div>
  <div class="item-content">{{ content_preview }}</div>
  <div class="item-footer">
    <span class="item-author">{{ author }}</span>
    <span class="item-time">{{ created_at_formatted }}</span>
  </div>
</div>
```

Content types map:
- `twitter` → blue tag
- `longform` → green tag
- `podcast` → purple tag
- `video` → gold tag
- anything else → gray tag

## Cron Integration

The website regeneration should run AFTER the main feed cron. Time spacing:

```
feed data collection: 8:00 / 20:00  (no_agent=True script)
website generation:   8:30 / 20:30  (no_agent=True script)
```

This ensures all recallers have completed before the website builds.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Site returns 401 | Root basic auth | Ensure `/feed` location has `auth_basic off` |
| Site returns 502 | Dashboard down but root points to it | `/feed` location should NOT proxy to dashboard (use `alias` to serve static files directly) |
| 404 on /feed/ | nginx alias path wrong | Check `/var/www/info-feed/` exists and has index.html |
| Filter not working | JS error | Check browser console for syntax errors in template |
