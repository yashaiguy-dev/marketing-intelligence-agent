#!/bin/bash
# YouTube Ads Spy — One-command installer
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing YouTube Ads Spy ==="
echo ""

# Step 1: Copy tool
echo "[1/3] Copying tool to ~/.claude/skills/youtube-ads-scraper/"
mkdir -p ~/.claude/skills/youtube-ads-scraper
cp "$SCRIPT_DIR/yt_ads_spy.py" ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py
echo "  Done ✓"

# Step 2: Install Python dependencies
echo ""
echo "[2/3] Installing Python dependencies..."
pip3 install requests patchright --quiet
python3 -m patchright install chromium
echo "  Done ✓"

# Step 3: Install skill file
echo ""
echo "[3/3] Adding skill to Claude Code..."
mkdir -p ~/.claude/commands
cp "$SCRIPT_DIR/youtube-ads-scraper.md" ~/.claude/commands/youtube-ads-scraper.md
echo "  Done ✓"

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Usage:"
echo "  • In Claude Code: type /youtube-ads-scraper or ask 'find YouTube ads for nike.com'"
echo "  • Standalone:     python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py \"nike.com\" --max-videos 10"
echo ""
echo "Optional — enable video transcription:"
echo "  export RAPIDAPI_KEY=\"your-key-here\"   # from rapidapi.com"
