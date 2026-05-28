# CDP Direct Extraction (Fallback)

When the Extension Service Worker approach fails (e.g. content script not injected, 
extension misconfigured, tab not found), fall back to direct DOM extraction via CDP
`Runtime.evaluate`.

## Approach

1. Navigate to URL via CDP (`Page.navigate`)
2. Wait for page load
3. Execute JavaScript in page context to extract content as markdown
4. Save to Clippings directory via `write_file`

## JS Extraction Code

```javascript
(async function() {
    await new Promise(r => setTimeout(r, 2000));
    var article = document.querySelector('article') || document.body;
    
    function extract(el, depth) {
        if (depth > 30 || !el || !el.tagName) return '';
        var t = el.tagName.toUpperCase();
        if (['SCRIPT','STYLE','NOSCRIPT','IFRAME','SVG'].includes(t)) return '';
        var r = '';
        for (var c of el.childNodes) {
            if (c.nodeType === 3) {
                var txt = (c.textContent||'').trim();
                if (txt) r += txt;
            } else if (c.nodeType === 1) {
                var ct = c.tagName.toUpperCase();
                var tx = extract(c, depth+1);
                if (!tx.trim()) continue;
                if (['H1','H2','H3','H4','H5','H6'].includes(ct))
                    r += '\\n' + '#'.repeat(parseInt(ct[1])) + ' ' + tx.trim() + '\\n\\n';
                else if (ct === 'P' || ct === 'DIV') r += tx.trim() + '\\n\\n';
                else if (ct === 'LI') r += '- ' + tx.trim() + '\\n';
                else if (ct === 'BLOCKQUOTE') r += '> ' + tx.trim().replace(/\\n/g,'\\n> ') + '\\n\\n';
                else if (['B','STRONG'].includes(ct)) r += '**' + tx.trim() + '** ';
                else if (['I','EM'].includes(ct)) r += '*' + tx.trim() + '* ';
                else r += tx;
            }
        }
        return r;
    }
    var md = extract(article, 0);
    return JSON.stringify({
        title: document.title, 
        content: md, 
        url: location.href
    });
})()
```

## Cookie Injection for Auth'd Sites

Before navigation, use `Network.setCookie`:

```python
await cdp(ws, "Network.setCookie", {
    "name": "auth_token",
    "value": session["authToken"],
    "domain": ".x.com",
    "path": "/",
    "secure": True,
    "httpOnly": True
})
await cdp(ws, "Network.setCookie", {
    "name": "ct0", 
    "value": session["ct0"],
    "domain": ".x.com",
    "path": "/",
    "secure": True
})
```

X.com requires: auth_token, ct0, guest_id.
Source file: `~/.config/xfetch/session.json`

## Quality Notes

- Public static pages (blogs, docs): excellent quality, 60+ KB typical
- X.com articles: ~4 KB, some noise (engagement buttons, empty lines)
- Heavy JS sites (SPA, paywalls): may need extra wait time
- NOT as polished as Obsidian Web Clipper output (no frontmatter templates, no custom formatting)
