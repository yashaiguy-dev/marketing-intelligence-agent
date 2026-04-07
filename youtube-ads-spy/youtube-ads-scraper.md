---
description: Scrape Google Ads Transparency for YouTube video ads and save results as Obsidian Markdown with thumbnails and transcripts
---

# YouTube Ads Scraper

When the user asks to scrape YouTube ads, find video ads, or get YouTube ads for a domain/advertiser, follow these steps:

## 1. Parse the request

Extract from the user's message:
- **Domain or advertiser** (required) — e.g. "nike.com", "apple.com", or a direct Google Ads Transparency URL
- **Max videos** (optional) — if the user specifies a number, use it; otherwise default to 20

## 2. Ask before running

Before running the scraper, confirm these with the user:
- **Output folder** — ask: "Where should I save the results? (default: `~/obsidian-vault/youtube-ads/`)"
- **Video transcription** — ask: "Do you want video transcripts? (requires RAPIDAPI_KEY env var)"

If the user says "just go" or doesn't specify, use the defaults (default folder, skip transcription if no env var set).

## 3. Run the scraper

Execute this command:

```bash
python3 ~/.claude/skills/youtube-ads-scraper/yt_ads_spy.py "<domain>" --max-videos <N> --output-dir "<output_folder>"
```

Replace `<domain>` with the parsed domain (keep original format).
Replace `<N>` with the max videos count (default 20 if not specified).
Replace `<output_folder>` with the user's chosen folder (default: `~/obsidian-vault/youtube-ads`).

**Important:** This launches a visible Chromium browser window. It takes 3-10 minutes depending on the number of videos. Do NOT set a short timeout — use at least 600000ms (10 minutes).

## 4. Report results

After the script finishes, tell the user:
- How many YouTube videos were found
- Where the Markdown file was saved
- Remind them they can open the folder as an Obsidian vault
- Each video includes: title, URL, view count, upload date, thumbnail, and transcript

Example: "Found 12 YouTube video ads for nike.com. Saved to `~/obsidian-vault/youtube-ads/nike-com/nike-com.md`. Each video has a thumbnail and collapsible transcript. You can open `~/obsidian-vault/youtube-ads/` as an Obsidian vault to browse them."
