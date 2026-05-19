#!/bin/bash
cd "$(dirname "$0")"

echo "============================================================"
echo "   ThunderFit - First-time setup (Mac)"
echo "============================================================"
echo ""

# Find python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 not installed."
    echo "Install from https://www.python.org/downloads/macos/"
    echo "or with Homebrew: brew install python"
    read -p "Press any key to close..."
    exit 1
fi

python3 --version
echo ""

echo "[..] Installing required packages..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user requests python-dotenv pillow streamlit playwright imageio-ffmpeg google-genai tavily-python
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install packages."
    read -p "Press any key to close..."
    exit 1
fi

echo ""
echo "============================================================"
echo "   [OK] Setup done!"
echo ""
echo "   Next: double-click  START_CHROME.command  then  APP_START.command"
echo "============================================================"
read -p "Press any key to close..."
