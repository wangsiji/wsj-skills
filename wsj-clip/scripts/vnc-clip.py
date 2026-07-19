#!/usr/bin/env python3
"""
VNC Clip: CDP + Extension Service Worker automation for Obsidian Web Clipper.
Navigates to URL via CDP, injects cookies for auth'd sites, triggers save
via chrome.tabs.sendMessage(tabId, {action: "saveMarkdownToFile"}).

Usage:
    python3 vnc-clip.py <URL>
    python3 vnc-clip.py https://x.com/user/status/123

Requires:
    - Chrome running with --remote-debugging-port=9222 (on DISPLAY :2)
    - Openbox WM running (DISPLAY=:2 openbox --replace &)
    - Obsidian Web Clipper extension installed in CDP profile
"""
import asyncio, json, sys, os, re as re2, urllib.request
import websockets
from datetime import datetime

CDP = "http://127.0.0.1:9222"
EXT_ID = "cnjifjpddelmedmihgijeibhnjfabmlf"
CLIPPING_DIR = "/home/wangsiji/projects/wsj-second-brain/00-LLM-WiKi/Raw"
CLIPPING_DIR_ALT = "/home/wangsiji/projects/wsj-second-brain/Inbox/00-LLM-WiKi/Raw/Clippings"
SESSION_FILE = "/home/wangsiji/.config/xfetch/session.json"


async def cdp_list():
    return json.loads(urllib.request.urlopen(f"{CDP}/json").read())


async def get_page_ws():
    tabs = await cdp_list()
    for t in tabs:
        u = t.get("url", "")
        if t["type"] == "page" and not u.startswith("chrome") and not u.startswith("devtools"):
            return t["webSocketDebuggerUrl"]
    return tabs[0]["webSocketDebuggerUrl"]


async def get_ext_ws():
    for t in await cdp_list():
        if EXT_ID in t.get("url", "") and t["type"] == "service_worker":
            return t["webSocketDebuggerUrl"]
    return None


async def cdp(ws, method, params=None):
    msg = {"id": 1, "method": method}
    if params: msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == 1:
            return resp


async def eval_js(ws, expr):
    r = await cdp(ws, "Runtime.evaluate", {
        "expression": expr, "returnByValue": True, "awaitPromise": True
    })
    v = r.get("result", {}).get("result", {})
    return None if v.get("subtype") == "error" else v.get("value")


async def wait_load(ws):
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("method") == "Page.loadEventFired":
            return


async def clip(url):
    # Step 1: Navigate via CDP
    page_ws = await get_page_ws()
    async with websockets.connect(page_ws, max_size=20*1024*1024) as ws:
        await cdp(ws, "Page.enable")
        await cdp(ws, "Runtime.enable")
        await cdp(ws, "Network.enable")

        # Inject cookies for auth'd sites
        if "x.com" in url or "twitter.com" in url:
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE) as f:
                    s = json.load(f)
                for n, v in [
                    ("auth_token", s.get("authToken", "")),
                    ("ct0", s.get("ct0", "")),
                    ("guest_id", "v1%3A1723456789"),
                ]:
                    await cdp(ws, "Network.setCookie", {
                        "name": n, "value": v, "domain": ".x.com",
                        "path": "/", "secure": True, "httpOnly": n == "auth_token",
                    })
                print(f"  [cookie] X.com auth injected")

        print(f"  [nav] {url}")
        await cdp(ws, "Page.navigate", {"url": url})
        await wait_load(ws)
        await asyncio.sleep(5)
        title = await eval_js(ws, "document.title")
        print(f"  [title] {title}")

    # Step 2: Connect to extension service worker
    ext_ws = await get_ext_ws()
    if not ext_ws:
        print("  [error] Extension SW not found! Is Clipper installed in CDP profile?")
        return

    async with websockets.connect(ext_ws, max_size=10*1024*1024) as sw:
        await cdp(sw, "Runtime.enable")

        # Find the correct tab
        tab_info = await eval_js(sw, f"""
        (async function() {{
            try {{
                var tabs = await chrome.tabs.query({{}});
                for (var t of tabs) {{
                    var u = t.url || '';
                    if (u.startsWith('http') && !u.startsWith('chrome-extension://')) {{
                        try {{ await chrome.tabs.sendMessage(t.id, {{action: "ping"}}); }}
                        catch(e) {{ continue; }}
                        return JSON.stringify({{tabId: t.id, url: u, title: t.title}});
                    }}
                }}
            }} catch(e) {{ return 'Error: ' + e.message; }}
        }})()
        """)
        if not tab_info or not tab_info.startswith("{"):
            print(f"  [error] No viable tab found: {tab_info}")
            return

        data = json.loads(tab_info)
        tab_id = data.get("tabId")

        # Check before
        before = set(os.listdir(CLIPPING_DIR)) if os.path.isdir(CLIPPING_DIR) else set()
        before_alt = set(os.listdir(CLIPPING_DIR_ALT)) if os.path.isdir(CLIPPING_DIR_ALT) else set()

        # Send save command
        result = await eval_js(sw, f"""
        (async function() {{
            try {{
                var response = await chrome.tabs.sendMessage({tab_id}, {{action: "saveMarkdownToFile"}});
                return JSON.stringify(response);
            }} catch(e) {{
                return 'Error: ' + e.message;
            }}
        }})()
        """)
        print(f"  [save] {result}")

        await asyncio.sleep(4)

        # Check both directories for new files
        after = set(os.listdir(CLIPPING_DIR)) if os.path.isdir(CLIPPING_DIR) else set()
        after_alt = set(os.listdir(CLIPPING_DIR_ALT)) if os.path.isdir(CLIPPING_DIR_ALT) else set()
        new_files = (after - before) | (after_alt - before_alt)
        if new_files:
            for f in new_files:
                if f in (after - before):
                    fp = os.path.join(CLIPPING_DIR, f)
                else:
                    fp = os.path.join(CLIPPING_DIR_ALT, f)
                print(f"  [done] {f} ({os.path.getsize(fp)} bytes)")
        else:
            print(f"  [fail] No new file in either {CLIPPING_DIR} or {CLIPPING_DIR_ALT}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 vnc-clip.py <URL>")
        sys.exit(1)
    asyncio.run(clip(sys.argv[1]))
