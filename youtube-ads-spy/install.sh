#!/bin/bash
# YouTube Ads Spy — One-command installer
# Supports: Claude Code, Qwen Code, standalone
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing YouTube Ads Spy ==="
echo ""

# Step 1: Install Python dependencies
echo "[1/3] Installing Python dependencies..."
pip3 install requests patchright --quiet
python3 -m patchright install chromium
echo "  Done ✓"

# Step 2: Detect and install for available AI CLIs
echo ""
echo "[2/3] Installing skill files..."

INSTALLED=""

# Claude Code
if [ -d "$HOME/.claude" ] || command -v claude &>/dev/null; then
    mkdir -p ~/.claude/skills/youtube-ads-scraper
    cp "$SCRIPT_DIR/yt_ads_spy.py" ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py
    mkdir -p ~/.claude/commands
    cp "$SCRIPT_DIR/youtube-ads-scraper.md" ~/.claude/commands/youtube-ads-scraper.md
    echo "  Claude Code ✓  (skill + command installed)"
    INSTALLED="$INSTALLED claude"
fi

# Qwen Code
if [ -d "$HOME/.qwen" ] || command -v qwen &>/dev/null; then
    mkdir -p ~/.qwen/skills/youtube-ads-scraper
    cp "$SCRIPT_DIR/yt_ads_spy.py" ~/.qwen/skills/youtube-ads-scraper/yt_ads_spy.py
    cp "$SCRIPT_DIR/SKILL.md" ~/.qwen/skills/youtube-ads-scraper/SKILL.md
    mkdir -p ~/.qwen/commands
    cp "$SCRIPT_DIR/youtube-ads-scraper.md" ~/.qwen/commands/youtube-ads-scraper.md
    echo "  Qwen Code ✓  (skill + command installed)"
    INSTALLED="$INSTALLED qwen"
fi

# Fallback: install for both if neither detected
if [ -z "$INSTALLED" ]; then
    echo "  No AI CLI detected. Installing for both Claude Code and Qwen Code..."
    mkdir -p ~/.claude/skills/youtube-ads-scraper ~/.claude/commands
    cp "$SCRIPT_DIR/yt_ads_spy.py" ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py
    cp "$SCRIPT_DIR/youtube-ads-scraper.md" ~/.claude/commands/youtube-ads-scraper.md
    mkdir -p ~/.qwen/skills/youtube-ads-scraper ~/.qwen/commands
    cp "$SCRIPT_DIR/yt_ads_spy.py" ~/.qwen/skills/youtube-ads-scraper/yt_ads_spy.py
    cp "$SCRIPT_DIR/SKILL.md" ~/.qwen/skills/youtube-ads-scraper/SKILL.md
    cp "$SCRIPT_DIR/youtube-ads-scraper.md" ~/.qwen/commands/youtube-ads-scraper.md
    echo "  Claude Code ✓"
    echo "  Qwen Code ✓"
fi

# Step 3: Verify
echo ""
echo "[3/3] Verifying installation..."
python3 -c "import requests; import patchright; print('  Dependencies OK ✓')"

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Usage:"
echo "  • Claude Code:  type /youtube-ads-scraper or ask 'find YouTube ads for nike.com'"
echo "  • Qwen Code:    type /youtube-ads-scraper or ask 'find YouTube ads for nike.com'"
echo "  • Standalone:   python3 yt_ads_spy.py \"nike.com\" --max-videos 10"
echo ""
echo "Optional — enable video transcription:"
echo "  export RAPIDAPI_KEY=\"your-key-here\"   # from rapidapi.com"
