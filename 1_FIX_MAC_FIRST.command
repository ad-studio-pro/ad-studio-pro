#!/bin/bash
# FIRST TIME on Mac: open Terminal manually and run:
#    cd ~/Documents/ad-studio-pro
#    bash FIX_MAC_PERMISSIONS.sh
# Then you can double-click the rest of the .command files.

cd "$(dirname "$0")"
bash FIX_MAC_PERMISSIONS.sh
echo ""
echo "Now you can double-click any .command file (1_SETUP, START_CHROME, APP_START)."
read -p "Press Enter to close..."
