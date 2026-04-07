#!/bin/bash
# Facebook Ads Spy — One-command installer
# Supports: Claude Code, Qwen Code, standalone
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Facebook Ads Spy ==="
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
    mkdir -p ~/.claude/skills/ads-spy
    cp "$SCRIPT_DIR/fb_ads_spy.py" ~/.claude/skills/ads-spy/fb_ads_spy.py
    mkdir -p ~/.claude/commands
    cp "$SCRIPT_DIR/ads-spy.md" ~/.claude/commands/ads-spy.md
    echo "  Claude Code ✓  (skill + command installed)"
    INSTALLED="$INSTALLED claude"
fi

# Qwen Code
if [ -d "$HOME/.qwen" ] || command -v qwen &>/dev/null; then
    mkdir -p ~/.qwen/skills/ads-spy
    cp "$SCRIPT_DIR/fb_ads_spy.py" ~/.qwen/skills/ads-spy/fb_ads_spy.py
    cp "$SCRIPT_DIR/SKILL.md" ~/.qwen/skills/ads-spy/SKILL.md
    mkdir -p ~/.qwen/commands
    cp "$SCRIPT_DIR/ads-spy.md" ~/.qwen/commands/ads-spy.md
    echo "  Qwen Code ✓  (skill + command installed)"
    INSTALLED="$INSTALLED qwen"
fi

# Fallback: install for both if neither detected
if [ -z "$INSTALLED" ]; then
    echo "  No AI CLI detected. Installing for both Claude Code and Qwen Code..."
    mkdir -p ~/.claude/skills/ads-spy ~/.claude/commands
    cp "$SCRIPT_DIR/fb_ads_spy.py" ~/.claude/skills/ads-spy/fb_ads_spy.py
    cp "$SCRIPT_DIR/ads-spy.md" ~/.claude/commands/ads-spy.md
    mkdir -p ~/.qwen/skills/ads-spy ~/.qwen/commands
    cp "$SCRIPT_DIR/fb_ads_spy.py" ~/.qwen/skills/ads-spy/fb_ads_spy.py
    cp "$SCRIPT_DIR/SKILL.md" ~/.qwen/skills/ads-spy/SKILL.md
    cp "$SCRIPT_DIR/ads-spy.md" ~/.qwen/commands/ads-spy.md
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
echo "  • Claude Code:  type /ads-spy or ask 'spy on Nike's Facebook ads'"
echo "  • Qwen Code:    type /ads-spy or ask 'spy on Nike's Facebook ads'"
echo "  • Standalone:   python3 fb_ads_spy.py \"Nike\" --max-ads 50"
echo ""
echo "Optional — enable video transcription:"
echo "  brew install ffmpeg"
echo "  export DEEPGRAM_API_KEY=\"your-key-here\"   # free at deepgram.com"
