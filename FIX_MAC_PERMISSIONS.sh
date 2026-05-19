#!/bin/bash
# Run this ONCE on Mac before opening any .command file.
# Bypasses macOS Gatekeeper for this folder only.

DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Removing macOS quarantine flags from $DIR ..."
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null
chmod +x "$DIR"/*.command 2>/dev/null
echo "✅ Done. You can now double-click the .command files."
