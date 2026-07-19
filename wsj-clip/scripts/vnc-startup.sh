#!/usr/bin/env bash
# VNC + Chrome CDP startup for vnc-clip.py
# Usage: bash scripts/vnc-startup.sh
# Runs: Xvfb :2 → openbox :2 → Chrome CDP on port 9222

set -e

DISPLAY_NUM="${1:-2}"
CDP_PORT="${2:-9222}"

echo "[startup] Starting VNC+Chrome for vnc-clip.py..."

# 1. Xvfb
if pgrep -a Xvfb | grep -q ":$DISPLAY_NUM"; then
    echo "  [skip] Xvfb already running on :$DISPLAY_NUM"
else
    echo "  [start] Xvfb :$DISPLAY_NUM ..."
    Xvfb ":$DISPLAY_NUM" -screen 0 1920x1080x24 &
    sleep 1
fi

# 2. Openbox
export DISPLAY=":$DISPLAY_NUM"
if pgrep -a openbox | grep -q ":$DISPLAY_NUM"; then
    echo "  [skip] openbox already running on :$DISPLAY_NUM"
else
    echo "  [start] openbox ..."
    openbox --replace &
    sleep 0.5
fi

# 3. Chrome with CDP
if curl -sf "http://127.0.0.1:$CDP_PORT/json/version" >/dev/null 2>&1; then
    echo "  [skip] Chrome CDP already running on port $CDP_PORT"
else
    echo "  [start] Chrome with CDP on port $CDP_PORT ..."
    google-chrome \
        --remote-debugging-port="$CDP_PORT" \
        --no-first-run --disable-gpu --disable-software-rasterizer \
        --user-data-dir="$HOME/.config/chrome-cdp" \
        --no-sandbox --disable-dev-shm-usage \
        >/dev/null 2>&1 &
    echo "  [wait] Waiting for Chrome to respond..."
    for i in $(seq 1 10); do
        if curl -sf "http://127.0.0.1:$CDP_PORT/json/version" >/dev/null 2>&1; then
            echo "  [ready] Chrome CDP ready"
            break
        fi
        sleep 1
    done
fi

echo "[startup] All services ready."
echo "  vnc-clip.py usage: python3 scripts/vnc-clip.py <URL>"
