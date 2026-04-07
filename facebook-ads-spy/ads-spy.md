---
description: Scrape Facebook Ad Library for an advertiser and save results as Obsidian Markdown
---

# Ads Spy

When the user asks to scrape Facebook ads, spy on ads, or get ads for an advertiser, follow these steps:

## 1. Parse the request

Extract from the user's message:
- **Advertiser name** (required) — the brand/company to search for
- **Max ads** (optional) — if the user specifies a number, use it; otherwise default to 200

## 2. Ask before running

Before running the scraper, confirm these with the user:
- **Output folder** — ask: "Where should I save the results? (default: `~/obsidian-vault/facebook-ads/`)"
- **Video transcription** — ask: "Do you want video ad transcripts? (requires DEEPGRAM_API_KEY env var and ffmpeg)"

If the user says "just go" or doesn't specify, use the defaults (default folder, skip transcription if no env var set).

## 3. Run the scraper

Execute this command:

```bash
python3 ~/.claude/skills/ads-spy/fb_ads_spy.py "<advertiser_name>" --max-ads <N> --output-dir "<output_folder>"
```

Replace `<advertiser_name>` with the parsed name (keep original casing).
Replace `<N>` with the max ads count (default 200 if not specified).
Replace `<output_folder>` with the user's chosen folder (default: `~/obsidian-vault/facebook-ads`).

**Important:** This launches a visible Chromium browser window. It takes 2-5 minutes depending on the number of ads. Do NOT set a short timeout — use at least 600000ms (10 minutes).

## 4. Report results

After the script finishes, tell the user:
- How many ads were found
- Where the Markdown file was saved
- Remind them they can open the folder as an Obsidian vault

Example: "Found 47 ads for Nike. Saved to `~/obsidian-vault/facebook-ads/nike/nike.md` with 52 images. You can open `~/obsidian-vault/facebook-ads/` as an Obsidian vault to browse them."
