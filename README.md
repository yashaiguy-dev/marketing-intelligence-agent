# Facebook Ads Spy — Claude Code Skill

Scrape any advertiser's Facebook ads from the Meta Ad Library. Downloads all ad creatives (images + videos), extracts landing URLs, ad copy, and optionally transcribes video ads — all saved as Obsidian-ready Markdown.

## What It Does

- Opens the Meta Ad Library in a real browser (anti-detection via Patchright)
- Searches for an advertiser and auto-scrolls to load all their ads
- Extracts: ad copy, landing URLs, images, videos, CTAs, start dates, platforms
- Downloads all media (images + videos) locally
- Optionally transcribes video ad audio using Deepgram
- Outputs everything as a clean Obsidian Markdown vault

## Requirements

- Python 3.8+
- macOS, Linux, or Windows
- Chrome/Chromium installed
- **Optional:** ffmpeg (for video audio extraction) + Deepgram API key (for transcription)

## Installation

### 1. Copy the tool

```bash
mkdir -p ~/.claude/skills/ads-spy
cp fb_ads_spy.py ~/.claude/skills/ads-spy/fb_ads_spy.py
```

### 2. Install dependencies

```bash
pip3 install requests patchright
python3 -m patchright install chromium
```

### 3. (Optional) Enable video transcription

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

Get a free Deepgram API key from [deepgram.com](https://deepgram.com) and set it:
```bash
export DEEPGRAM_API_KEY="your-key-here"
```

Add the export to your `~/.zshrc` or `~/.bashrc` to make it permanent.

### 4. Add the skill to Claude Code

```bash
mkdir -p ~/.claude/commands
cp ads-spy.md ~/.claude/commands/ads-spy.md
```

### 5. Done

Open Claude Code and type `/ads-spy` or just ask "spy on Nike's Facebook ads".

## Standalone Usage (Without Claude Code)

Works as a standalone CLI tool with any AI coding assistant or directly from terminal:

```bash
# Basic usage
python3 ~/.claude/skills/ads-spy/fb_ads_spy.py "Nike"

# Limit to 50 ads
python3 ~/.claude/skills/ads-spy/fb_ads_spy.py "Nike" --max-ads 50

# Custom output directory
python3 ~/.claude/skills/ads-spy/fb_ads_spy.py "Nike" --output-dir ~/my-ads
```

## Output Structure

```
~/obsidian-vault/facebook-ads/
└── nike/
    ├── nike.md           ← Main Markdown file with all ads
    ├── images/           ← Downloaded ad images
    │   ├── ad-1-1.jpg
    │   └── ad-2-1.jpg
    ├── videos/           ← Downloaded ad videos
    │   └── ad-3-1.mp4
    └── audio/            ← Extracted audio + transcripts
        └── ad-3-1.mp3
```

Open `~/obsidian-vault/facebook-ads/` as an Obsidian vault to browse everything with embedded images and videos.

## Using with Other AI CLI Tools

The Python script works standalone — you can use it with any AI assistant:

**Gemini CLI / Qwen / other AI CLIs:**
Just tell your AI: "Run `python3 path/to/fb_ads_spy.py "BrandName"` and report the results."

**Direct terminal:**
```bash
python3 fb_ads_spy.py "Coca-Cola" --max-ads 100
```

## Tips

- The scraper uses **Patchright** (anti-detection Playwright) to avoid Meta's bot detection
- First run may take longer as it downloads Chromium
- Video transcription requires both ffmpeg and a Deepgram API key — without them, ads still scrape fine, just no transcripts
- The browser opens visibly so you can watch the scraping happen
- If interrupted (Ctrl+C), partial results are still saved
