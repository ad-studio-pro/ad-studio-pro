#!/bin/bash
cd "$(dirname "$0")"

CDP_PORT="${CDP_PORT:-9224}"
CDP_PROFILE="$HOME/thunderfit-cdp-profile"

echo ""
echo "=== Opening dedicated Chrome for ThunderFit Ad Studio ==="
echo "Port    : $CDP_PORT"
echo "Profile : $CDP_PROFILE"
echo ""

CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -f "$CHROME_APP" ]; then
    echo "[ERROR] Google Chrome not found at $CHROME_APP"
    echo "Install Chrome from https://www.google.com/chrome/"
    read -p "Press any key to close..."
    exit 1
fi

mkdir -p "$CDP_PROFILE"

"$CHROME_APP" \
    --remote-debugging-port=$CDP_PORT \
    --remote-debugging-address=127.0.0.1 \
    --user-data-dir="$CDP_PROFILE" \
    --no-default-browser-check \
    --no-first-run \
    https://claude.ai/new &

sleep 4

echo "Verifying CDP port $CDP_PORT is listening..."
if lsof -iTCP:$CDP_PORT -sTCP:LISTEN -n 2>/dev/null | grep -q LISTEN; then
    echo "[OK] CDP is listening on port $CDP_PORT"
else
    echo "[WARN] Port $CDP_PORT not listening yet. Wait 10s and try CHECK_CHROME.command"
fi

echo ""
echo "=== FIRST TIME ONLY ==="
echo "  1. In the new Chrome window, log in to claude.ai"
echo "  2. Switch model to 'Opus 4.7' (avoid 'Adaptive')"
echo "  3. Keep this Chrome window OPEN while using the app"
echo ""
echo "You can close this Terminal window — Chrome will keep running."
echo ""
read -p "Press any key to close..."
