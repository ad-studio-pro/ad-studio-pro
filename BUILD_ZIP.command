#!/bin/bash
cd "$(dirname "$0")"
SRC="$(pwd)"
STAMP=$(date +%Y%m%d_%H%M)

echo "=== Building zips (your outputs/ folder stays untouched) ==="

cd "$(dirname "$SRC")"
DIR_NAME=$(basename "$SRC")

ZIP_FULL="$HOME/Documents/ad-studio-pro-FULL-${STAMP}.zip"
ZIP_NOKEYS="$HOME/Documents/ad-studio-pro-NOKEYS-${STAMP}.zip"

# FULL with .env
zip -ry "$ZIP_FULL" "$DIR_NAME" \
    -x "$DIR_NAME/outputs/videos/*.mp4" \
    -x "$DIR_NAME/outputs/logs/*.json" \
    -x "$DIR_NAME/outputs/thumbnails/*" \
    -x "$DIR_NAME/__pycache__/*" \
    -x "$DIR_NAME/scripts/__pycache__/*" \
    -x "$DIR_NAME/venv/*" \
    -x "*.pyc" -x "*.DS_Store" > /dev/null

# NOKEYS without .env
zip -ry "$ZIP_NOKEYS" "$DIR_NAME" \
    -x "$DIR_NAME/.env" \
    -x "$DIR_NAME/outputs/videos/*.mp4" \
    -x "$DIR_NAME/outputs/logs/*.json" \
    -x "$DIR_NAME/outputs/thumbnails/*" \
    -x "$DIR_NAME/__pycache__/*" \
    -x "$DIR_NAME/scripts/__pycache__/*" \
    -x "$DIR_NAME/venv/*" \
    -x "*.pyc" -x "*.DS_Store" > /dev/null

echo "FULL:   $ZIP_FULL  ($(ls -lh "$ZIP_FULL" | awk '{print $5}'))"
echo "NOKEYS: $ZIP_NOKEYS  ($(ls -lh "$ZIP_NOKEYS" | awk '{print $5}'))"
echo "Done."
read -p "Press Enter to close..."
