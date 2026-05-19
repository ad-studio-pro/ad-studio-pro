#!/bin/bash
cd "$(dirname "$0")"

CDP_PORT="${CDP_PORT:-9224}"

echo "============================================================"
echo "   Chrome CDP Diagnostic — port $CDP_PORT"
echo "============================================================"
echo ""

echo "[1] Is anything listening on port $CDP_PORT?"
echo "----------------------------------------"
lsof -iTCP:$CDP_PORT -sTCP:LISTEN -n 2>/dev/null
if [ $? -ne 0 ] || ! lsof -iTCP:$CDP_PORT -sTCP:LISTEN -n 2>/dev/null | grep -q LISTEN; then
    echo "  NOTHING listening on $CDP_PORT."
    echo "  -> Run START_CHROME.command first."
fi
echo ""

echo "[2] Can we reach http://127.0.0.1:$CDP_PORT/json/version ?"
echo "-----------------------------------------------------"
curl -s -o /dev/null -w "  HTTP %{http_code}  (response time %{time_total}s)\n" http://127.0.0.1:$CDP_PORT/json/version
echo ""

echo "[3] Chrome processes with --remote-debugging-port flag:"
echo "-----------------------------------------------------"
ps aux | grep -i "chrome.*remote-debugging-port" | grep -v grep | head -3
echo ""

echo "============================================================"
echo "If port is not listening:"
echo "  1. Quit ALL Chrome windows (Cmd+Q on Chrome)"
echo "  2. Open Activity Monitor — kill any 'Google Chrome' process"
echo "  3. Run START_CHROME.command again"
echo "============================================================"
read -p "Press any key to close..."
