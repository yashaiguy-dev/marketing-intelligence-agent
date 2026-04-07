#!/bin/bash
# Facebook Ads Spy — One-command installer
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Facebook Ads Spy ==="
echo ""

# Step 1: Copy tool
echo "[1/3] Copying tool to ~/.claude/skills/ads-spy/"
mkdir -p ~/.claude/skills/ads-spy
cp "$SCRIPT_DIR/fb_ads_spy.py" ~/.claude/skills/ads-spy/fb_ads_spy.py
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
cp "$SCRIPT_DIR/ads-spy.md" ~/.claude/commands/ads-spy.md
echo "  Done ✓"

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Usage:"
echo "  • In Claude Code: type /ads-spy or ask 'spy on Nike's Facebook ads'"
echo "  • Standalone:     python3 ~/.claude/skills/ads-spy/fb_ads_spy.py \"Nike\" --max-ads 50"
echo ""
echo "Optional — enable video transcription:"
echo "  brew install ffmpeg"
echo "  export DEEPGRAM_API_KEY=\"your-key-here\"   # free at deepgram.com"
