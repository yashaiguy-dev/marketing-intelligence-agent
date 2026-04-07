# YouTube Ads Spy — Claude Code Skill

Find any brand's YouTube video ads from the Google Ads Transparency Center. Extracts video metadata, thumbnails, view counts, and transcripts — all saved as Obsidian-ready Markdown.

## What It Does

- Searches Google Ads Transparency Center for an advertiser's video ads
- Filters to YouTube video format automatically
- Extracts: video title, URL, view count, upload date
- Embeds YouTube thumbnails (permanent, never expire)
- Fetches full video transcripts via RapidAPI (optional)
- Outputs clean Obsidian Markdown with collapsible transcripts
- Uses Patchright (anti-detection) to bypass bot protection

## Requirements

- Python 3.8+
- macOS, Linux, or Windows
- Chrome/Chromium installed

## Installation

### 1. Copy the tool

```bash
mkdir -p ~/.claude/skills/youtube-ads-scraper
cp yt_ads_spy.py ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py
```

### 2. Install dependencies

```bash
pip3 install requests patchright
python3 -m patchright install chromium
```

### 3. (Optional) Enable video transcription

Get a RapidAPI key and subscribe to the [YouTube Transcript API](https://rapidapi.com/ytjar/api/youtube-transcript3):

```bash
export RAPIDAPI_KEY="your-key-here"
```

Add the export to your `~/.zshrc` or `~/.bashrc` to make it permanent.

Without this, everything works — you just won't get transcripts.

### 4. Add the skill to Claude Code

```bash
mkdir -p ~/.claude/commands
cp youtube-ads-scraper.md ~/.claude/commands/youtube-ads-scraper.md
```

### 5. Done

Open Claude Code and type `/youtube-ads-scraper` or just ask: "Find YouTube ads for nike.com"

## Standalone Usage (Without Claude Code)

Works as a standalone CLI tool with any AI coding assistant or directly from terminal:

```bash
# Basic usage
python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py "nike.com"

# Limit to 10 videos
python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py "nike.com" --max-videos 10

# Custom output directory
python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py "nike.com" --output-dir ~/my-ads

# Direct Google Ads Transparency URL
python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py "https://adstransparency.google.com/advertiser/AR12345678"
```

## Output Structure

```
~/obsidian-vault/youtube-ads/
└── nike-com/
    └── nike-com.md           ← Markdown with all videos
```

Each video in the Markdown includes:
- Title and YouTube URL
- View count (formatted: 1.2M, 45.3K)
- Upload date
- Embedded thumbnail (YouTube CDN, never expires)
- Collapsible transcript (if RapidAPI key is set)

Open `~/obsidian-vault/youtube-ads/` as an Obsidian vault to browse everything.

## Using with Other AI CLI Tools

The Python script works standalone — use it with any AI assistant:

**Gemini CLI / Qwen / other AI CLIs:**
Just tell your AI: "Run `python3 path/to/yt_ads_spy.py "brand.com"` and report the results."

**Direct terminal:**
```bash
python3 yt_ads_spy.py "coca-cola.com" --max-videos 15
```

## Tips

- **Default is 20 videos** — specify `--max-videos` to change
- **Scraping takes 3-10 minutes** — it drives a real browser through Google Ads Transparency
- **Thumbnails never expire** — they link to YouTube's CDN, not temporary URLs
- **Transcripts are optional** — the tool works without a RapidAPI key, just no transcripts
- **Supports direct URLs** — paste a Google Ads Transparency advertiser URL directly
- **If interrupted (Ctrl+C)** — partial results are still saved
